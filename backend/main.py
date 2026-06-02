# ============================================
# 抖音直播运营智能决策分析系统 — 主程序 v3.0
# ============================================
# 运行方式：python backend/main.py
#
# 技术栈: DrissionPage + FastAPI + WebSocket + Vue3 + ECharts
#
# 升级变更（v1.0 → v3.0）：
#   - 新增服务模块拆分（services/）
#   - 新增运营指标计算（满意度、热度、风险等级）
#   - 新增业务关注主题 TOP5
#   - 新增异常预警中心
#   - 新增 AI 运营建议（规则引擎）
#   - WebSocket 数据结构兼容升级
# ============================================

import asyncio
import atexit
import logging
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import sys as _sys

# 抑制 jieba 启动时的 print 输出
class _Silence:
    def write(self, *_): pass
    def flush(self, *_): pass
_orig_stdout = _sys.stdout
_sys.stdout = _Silence()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from collector import run_danmu_monitor

# 恢复输出
_sys.stdout = _orig_stdout

# ========== 服务模块导入 ==========
from services.sentiment_service import SentimentService
from services.metrics_service import MetricsService
from services.warning_service import WarningService
from services.advice_service import AdviceService

# ========== 日志配置 ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger("liveops")

# ========== 全局变量 ==========
danmu_queue: queue.Queue = queue.Queue()
connected_clients: set[WebSocket] = set()
_browser_ref: list = []        # 用于存储 browser 引用
_vite_ref: list = []  # [Popen] Vite 前端进程引用，用 list 包装避免 global 冲突

# ========== 前端自动启动 ==========
def start_vite() -> subprocess.Popen | None:
    """
    自动启动 Vite 前端开发服务器

    在后端启动前拉起前端，用户只需运行 python main.py 即可。
    返回 Popen 对象供 cleanup 时终止。
    """
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    frontend_dir = os.path.abspath(frontend_dir)

    if not os.path.isdir(frontend_dir):
        logger.warning(f"[前端启动] 目录不存在: {frontend_dir}")
        return None

    # 检查 node_modules
    if not os.path.isdir(os.path.join(frontend_dir, "node_modules")):
        logger.info("[前端启动] 正在安装前端依赖 (npm install)...")
        try:
            subprocess.run(
                "npm install",
                cwd=frontend_dir,
                shell=True,
                check=True,
                capture_output=True,
                timeout=120
            )
            logger.info("[前端启动] 依赖安装完成")
        except subprocess.TimeoutExpired:
            logger.error("[前端启动] npm install 超时")
            return None
        except Exception as e:
            logger.error(f"[前端启动] npm install 失败: {e}")
            return None

    # 启动 Vite（先清端口残留）
    try:
        # 杀掉可能残留的旧 Vite 进程
        _kill_node_processes()
        logger.info("[前端启动] 正在启动 Vite 开发服务器...")
        proc = subprocess.Popen(
            "npx vite --host 127.0.0.1 --port 5173",
            cwd=frontend_dir,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        time.sleep(1.5)
        logger.info("[前端启动] Vite 已启动 → http://127.0.0.1:5173")
        return proc
    except Exception as e:
        logger.error(f"[前端启动] 启动失败: {e}")
        return None


def _kill_node_processes() -> None:
    """杀掉所有 node 进程释放端口"""
    try:
        subprocess.run(
            "taskkill /F /IM node.exe",
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
        )
    except Exception:
        pass


def stop_vite(proc: subprocess.Popen | None) -> None:
    """终止 Vite 进程及其子进程"""
    if proc is None:
        return
    try:
        proc.kill()
        proc.wait(timeout=5)
        logger.info("[前端启动] Vite 进程已终止")
    except Exception:
        pass
    # 二次确保清端口
    _kill_node_processes()


# ========== 服务实例化 ==========
sentiment_service = SentimentService(window_size=100)
metrics_service = MetricsService()
warning_service = WarningService(cooldown_seconds=120)
advice_service = AdviceService()

# ========== 运营数据缓存 ==========
# 用于在前端重连时发送最新快照
latest_metrics: Dict = {
    "satisfaction": 50.0,
    "heat_index": 0.0,
    "risk_level": "低",
}
latest_topics: List[Dict] = []
latest_warnings: List[Dict] = []
latest_advice: List[str] = []
# v3.0 新增缓存
latest_warning_status: Dict = {
    "level": "🟢", "level_text": "正常", "negative_rate": 0.0,
    "keywords": [], "count": 0, "change_5min": "0%", "timestamp": "",
}
latest_structured_advice: Dict = {
    "topic": "等待数据分析...", "hotwords": [], "advice": [],
}

# ========== FastAPI 生命周期 ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化后台任务"""
    asyncio.create_task(broadcast_danmu())
    asyncio.create_task(periodic_metrics_push())
    logger.info("[系统] FastAPI 启动完成，后台任务已就绪")
    logger.info("[系统] 服务: 情绪分析 | 指标计算 | 预警检测 | 建议生成")
    yield

# ========== FastAPI 初始化 ==========
app = FastAPI(
    title="抖音直播运营智能决策分析系统",
    description="基于 DrissionPage + FastAPI + WebSocket + Vue3 + ECharts 的直播运营决策分析平台",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """健康检查 + 系统状态"""
    return {
        "status": "运行中",
        "service": "抖音直播运营智能决策分析系统",
        "version": "3.0.0",
        "websocket": "ws://127.0.0.1:8000/ws",
        "connected_clients": len(connected_clients),
        "metrics": latest_metrics,
        # v3.0 新增
        "warning_status": latest_warning_status,
        "structured_advice": latest_structured_advice,
    }


@app.get("/api/metrics")
async def get_metrics():
    """获取最新运营指标（HTTP 轮询备用）"""
    return {
        "metrics": latest_metrics,
        "topics": latest_topics,
        "warnings": latest_warnings,
        "advice": latest_advice,
        # v3.0 新增：统一预警与建议 JSON
        "warning_status": latest_warning_status,
        "structured_advice": latest_structured_advice,
    }


# ========== WebSocket ==========
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端点 — 实时推送运营分析数据

    数据结构（v3.0 兼容升级）：
    {
        // === v1.0 原有字段（保持不变，保证旧功能正常） ===
        "type": "danmu",
        "name": "用户",
        "content": "弹幕内容",
        "words": ["词1", "词2"],
        "sentiment": "positive",
        "realtime_sentiment": {"positive": N, "neutral": N, "negative": N},
        "global_sentiment": {"positive": N, "neutral": N, "negative": N},
        "time": "HH:MM:SS",

        // === v3.0 新增字段 ===
        "metrics": {
            "satisfaction": 83.0,     // 满意度 0~100
            "heat_index": 76.0,       // 热度指数 0~100
            "risk_level": "中",        // 风险等级 低/中/高
        },
        "topics": [                    // 关注主题 TOP5
            {"name": "价格", "count": 120},
            ...
        ],
        "warnings": [                  // 异常预警
            {"level": "high", "type": "price", "message": "..."},
            ...
        ],
        "advice": [                    // 运营建议
            "建议说明优惠政策",
            ...
        ],
        "sentiment_timeline": {        // 情绪趋势（30分钟窗口）
            "timeline": ["14:30:00", ...],
            "positive": [N, ...],
            "neutral": [N, ...],
            "negative": [N, ...],
        }
    }
    """
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"[WebSocket] 新客户端连接，当前连接数: {len(connected_clients)}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("[WebSocket] 客户端正常断开")
    except Exception as e:
        logger.error(f"[WebSocket] 连接异常: {e}")
    finally:
        connected_clients.discard(websocket)
        logger.info(f"[WebSocket] 客户端断开，当前连接数: {len(connected_clients)}")


# ========== 情绪趋势时间线（30分钟窗口） ==========
# 每30秒采样一次，记录过去30分钟的情绪分布
_sentiment_timeline: Dict[str, List] = {
    "timeline": [],
    "positive": [],
    "neutral": [],
    "negative": [],
}
_last_timeline_sample: float = 0.0
TIMELINE_INTERVAL: float = 30.0  # 30秒采样一次
MAX_TIMELINE_POINTS: int = 60    # 30分钟 / 30秒 = 60个点


def _update_sentiment_timeline(now: float) -> None:
    """每30秒将当前情绪快照写入时间线"""
    global _last_timeline_sample, _sentiment_timeline

    if now - _last_timeline_sample < TIMELINE_INTERVAL:
        return
    _last_timeline_sample = now

    rt = sentiment_service.get_realtime()
    time_str = time.strftime("%H:%M:%S", time.localtime(now))

    _sentiment_timeline["timeline"].append(time_str)
    _sentiment_timeline["positive"].append(rt.get("positive", 0))
    _sentiment_timeline["neutral"].append(rt.get("neutral", 0))
    _sentiment_timeline["negative"].append(rt.get("negative", 0))

    # 保持最多 60 个点
    for key in ("timeline", "positive", "neutral", "negative"):
        while len(_sentiment_timeline[key]) > MAX_TIMELINE_POINTS:
            _sentiment_timeline[key].pop(0)


# ========== 广播协程 ==========
async def broadcast_danmu():
    """
    后台协程：持续从队列取弹幕，经服务处理后广播给所有 WebSocket 客户端

    处理流程：
        1. 从队列取出原始弹幕数据（collector 已含情绪分析结果）
        2. 喂入各服务进行指标计算（满意度 / 热度 / 风险 / 主题 / 预警）
        3. 组装完整的 WebSocket 消息（v1.0 兼容 + v3.0 扩展）
        4. 广播给所有连接的客户端
    """
    logger.info("[广播任务] 弹幕广播协程已启动（每 0.1 秒轮询一次）")

    while True:
        try:
            try:
                danmu_data: dict = danmu_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.1)
                continue

            now: float = time.time()

            # ---- 1. 提取 collector 已计算的数据（保持与 v1.0 一致） ----
            sentiment_label: str = danmu_data.get("sentiment", "neutral")
            content: str = danmu_data.get("content", "")

            # 使用 collector 提供的情绪分布（单一数据源，避免双重计数）
            realtime_sent: Dict[str, int] = danmu_data.get("realtime_sentiment", {"positive": 0, "neutral": 0, "negative": 0})
            global_sent: Dict[str, int] = danmu_data.get("global_sentiment", {"positive": 0, "neutral": 0, "negative": 0})

            # 同步 sentiment_service（供定期推送时使用）
            sentiment_service.global_stats = dict(global_sent)
            sentiment_service._realtime_queue.clear()
            for _ in range(realtime_sent.get("positive", 0)):
                sentiment_service._realtime_queue.append("positive")
            for _ in range(realtime_sent.get("neutral", 0)):
                sentiment_service._realtime_queue.append("neutral")
            for _ in range(realtime_sent.get("negative", 0)):
                sentiment_service._realtime_queue.append("negative")

            # ---- 2. 喂入指标服务 ----
            metrics_service.record_danmu()  # 记录弹幕时间戳（用于热度计算）

            # 记录业务关键词
            business_words: Dict[str, int] = danmu_data.get("business_words", {})
            if business_words:
                for topic_name, cnt in business_words.items():
                    metrics_service._business_topic_counts[topic_name] += cnt

            # ---- 3. 喂入预警服务（v3.0 兼容 + v3.0 升级） ----
            user_name: str = danmu_data.get("name", "")
            warning_service.scan_danmu(content, user_name)

            # ---- v3.0：更新负面率并获取预警状态 ----
            neg_count: int = realtime_sent.get("negative", 0)
            total_count: int = sum(realtime_sent.values()) or 1
            neg_rate: float = neg_count / total_count
            warning_service.update_negative_rate(neg_rate, neg_count, total_count)
            warning_status: Dict = warning_service.get_warning_status()

            # ---- 4. 计算运营指标 ----
            satisfaction: float = metrics_service.calc_satisfaction(realtime_sent)
            heat_index: float = metrics_service.calc_heat_index()
            risk_level: str = metrics_service.calc_risk_level(realtime_sent)
            topics: List[Dict] = metrics_service.get_top_topics(5)
            new_warnings: List[Dict] = warning_service.check_warnings()
            active_warnings: List[Dict] = warning_service.get_active_warnings()
            topic_counts: Dict[str, int] = dict(metrics_service._business_topic_counts)

            # ---- v3.0 指标驱动建议（向后兼容） ----
            advice: List[str] = advice_service.generate(
                sentiment_stats=realtime_sent,
                satisfaction=satisfaction,
                heat_index=heat_index,
                risk_level=risk_level,
                topic_counts=topic_counts,
                warnings=active_warnings,
            )

            # ---- v3.0 热词驱动结构化建议 ----
            danmu_words: List[str] = danmu_data.get("words", [])
            warning_keywords: List[str] = warning_status.get("keywords", [])
            structured_advice: Dict = advice_service.generate_structured(
                hotwords=danmu_words,
                extra_hotwords=warning_keywords,
            )

            # ---- 5. 更新情绪时间线 ----
            _update_sentiment_timeline(now)

            # ---- 6. 缓存最新数据 ----
            latest_metrics.update({
                "satisfaction": satisfaction,
                "heat_index": heat_index,
                "risk_level": risk_level,
            })
            global latest_topics, latest_warnings, latest_advice
            latest_topics = topics
            latest_warnings = active_warnings[:10]
            latest_advice = advice

            # v3.0 新增缓存
            global latest_warning_status, latest_structured_advice
            latest_warning_status = warning_status
            latest_structured_advice = structured_advice

            # ---- 7. 组装 WebSocket 消息（兼容 v1.0/v3.0 所有字段） ----
            message: dict = {
                # === v1.0 原有字段（完全兼容） ===
                "type": danmu_data.get("type", "danmu"),
                "name": danmu_data.get("name", ""),
                "content": content,
                "words": danmu_data.get("words", []),
                "sentiment": sentiment_label,
                "realtime_sentiment": realtime_sent,
                "global_sentiment": global_sent,
                "time": danmu_data.get("time", ""),
                # === v3.0 新增字段 ===
                "metrics": {
                    "satisfaction": satisfaction,
                    "heat_index": heat_index,
                    "risk_level": risk_level,
                },
                "topics": topics,
                "warnings": active_warnings[:10],
                "advice": advice,
                # === v3.0 新增：统一预警与建议 JSON ===
                "warning_status": warning_status,
                "structured_advice": structured_advice,
            }

            if new_warnings:
                message["new_warnings"] = new_warnings

            # ---- 8. 广播给所有客户端 ----
            if not connected_clients:
                continue

            disconnected: set[WebSocket] = set()
            for client in connected_clients:
                try:
                    await client.send_json(message)
                except Exception:
                    disconnected.add(client)

            if disconnected:
                connected_clients.difference_update(disconnected)

        except Exception as e:
            logger.error(f"[广播异常] {e}", exc_info=True)
            await asyncio.sleep(1)


# ========== 定期推送协程（无弹幕时也推送指标更新） ==========
async def periodic_metrics_push():
    """
    即使没有新弹幕，也定期推送运营指标和情绪时间线
    确保大屏数据保持刷新
    """
    logger.info("[定期推送] 指标定时推送协程已启动（每5秒一次）")

    while True:
        await asyncio.sleep(5)

        if not connected_clients:
            continue

        try:
            now: float = time.time()

            # 更新情绪时间线
            _update_sentiment_timeline(now)

            realtime_sent = sentiment_service.get_realtime()
            satisfaction: float = metrics_service.calc_satisfaction(realtime_sent)
            heat_index: float = metrics_service.calc_heat_index()
            risk_level: str = metrics_service.calc_risk_level(realtime_sent)
            active_warnings: List[Dict] = warning_service.get_active_warnings()

            latest_metrics.update({
                "satisfaction": satisfaction,
                "heat_index": heat_index,
                "risk_level": risk_level,
            })

            # v3.0 预警状态
            warning_status: Dict = warning_service.get_warning_status()

            message: dict = {
                "type": "metrics_snapshot",
                "metrics": {
                    "satisfaction": satisfaction,
                    "heat_index": heat_index,
                    "risk_level": risk_level,
                },
                "sentiment_timeline": dict(_sentiment_timeline),
                "warnings": active_warnings[:10],
                "realtime_sentiment": realtime_sent,
                "time": time.strftime("%H:%M:%S", time.localtime(now)),
                # v3.0 新增
                "warning_status": warning_status,
            }

            disconnected: set[WebSocket] = set()
            for client in connected_clients:
                try:
                    await client.send_json(message)
                except Exception:
                    disconnected.add(client)

            if disconnected:
                connected_clients.difference_update(disconnected)

        except Exception as e:
            logger.error(f"[定期推送异常] {e}", exc_info=True)


# ========== 清理 ==========
def cleanup():
    """退出时清理浏览器进程、前端进程和所有服务状态"""
    try:
        # 终止 Vite 前端进程
        # 终止 Vite 前端进程
        stop_vite(_vite_ref[0] if _vite_ref else None)

        # 清理服务状态
        sentiment_service.reset()
        metrics_service.reset()
        warning_service.reset()
        advice_service.reset()
        logger.info("[清理] 服务状态已重置")

        if _browser_ref:
            logger.info("[清理] 正在关闭浏览器...")
            _browser_ref[0].quit()
            _browser_ref.clear()
            logger.info("[清理] 浏览器已关闭")
    except Exception as e:
        logger.error(f"[清理] 异常: {e}")


# ========== 入口 ==========
if __name__ == '__main__':
    # 修复 Windows 控制台 GBK 编码不支持 emoji 的问题
    sys.stdout.reconfigure(encoding='utf-8')

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))

    print()
    print("  ⏳ 正在加载模型...")
    print("=" * 60)
    print("    📊  抖音直播运营智能决策分析系统 v3.0")
    print("    🎯  技术栈: DrissionPage + FastAPI + WebSocket + Vue3 + ECharts")
    print("    📦  服务: 情绪分析 | 指标计算 | 预警检测 | 建议生成")
    print("=" * 60)
    print()

    # 输入直播间地址
    print("━" * 60)
    print("  支持链接格式示例：")
    print("    https://live.douyin.com/123456789")
    print("  （长链接会自动精简，直接粘贴即可）")
    print("━" * 60)
    print()

    # 非交互模式（如 VS Code 的 Output 面板）检测
    if not sys.stdin.isatty():
        print("=" * 60)
        print("❌ 检测到非交互式终端（如 VS Code 输出面板）")
        print()
        print("👉 请在 VS Code 底部 TERMINAL(终端) 面板中输入:")
        print("   python backend/main.py")
        print()
        print("   不要使用右上角 ▶ Run 按钮!")
        print("=" * 60)
        exit(1)

    live_url = ""
    while not live_url:
        raw = input("请输入抖音直播间地址：").strip()
        # 自动精简：只保留到直播间 ID，去掉 ? 后面的参数
        if "live.douyin.com" in raw and "?" in raw:
            raw = raw.split("?")[0]
            print(f"  → 自动精简为: {raw}")
        if not raw:
            print("  ⚠️ 地址不能为空，请重新输入")
            continue
        if "live.douyin.com" not in raw:
            print("  ⚠️ 不是抖音直播间链接，请重新输入")
            continue
        live_url = raw

    print()

    # 启动弹幕监听线程
    monitor_thread = threading.Thread(
        target=run_danmu_monitor,
        args=(live_url, danmu_queue, _browser_ref),
        daemon=True,
        name="DanmuMonitorThread"
    )
    monitor_thread.start()
    print("[主线程] 弹幕监听线程已启动")

    print("-" * 60)
    print("系统启动中...")
    print("-" * 60)
    # 自动启动前端 Vite 开发服务器
    _vite_ref.clear()
    proc = start_vite()
    if proc:
        _vite_ref.append(proc)

    print("[主线程] FastAPI 服务器启动中...")
    print()
    print("=" * 60)
    print("  ✅ 服务已启动！")
    print("  📡 WebSocket 地址: ws://127.0.0.1:8000/ws")
    print("  🌐 后端 API 地址:  http://127.0.0.1:8000")
    print("  🎨 前端地址:       http://127.0.0.1:5173")
    print("  📖 API 文档地址:   http://127.0.0.1:8000/docs")
    print()
    print("  💡 系统功能:")
    print("     • 满意度评分   — 基于情绪分布实时计算")
    print("     • 热度指数     — 基于弹幕频率实时计算")
    print("     • 风险等级     — 基于负面占比实时判定")
    print("     • 关注主题TOP5 — 基于业务关键词聚合")
    print("     • 异常预警     — 基于阈值规则实时检测")
    print("     • 运营建议     — 基于规则引擎自动生成")
    print()
    print("  按 Ctrl+C 停止服务器")
    print("=" * 60)

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
