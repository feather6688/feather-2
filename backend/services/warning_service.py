# ============================================
# 异常预警服务 v3.0 — 四等级预警 + 负面关键词分析
# ============================================
# 功能：
#   1. 四等级预警：🟢正常 / 🟡关注 / 🟠预警 / 🔴严重
#   2. 负面情绪率实时追踪（分钟级采样）
#   3. 负面弹幕关键词统计（如卡顿、掉帧、延迟）
#   4. 与5分钟前的关键词数量变化对比
#   5. 保留 v2.0 业务关键词预警规则（向后兼容）
# ============================================

import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


# ========== v3.0 负面关键词词库（直播技术类） ==========
NEGATIVE_KEYWORDS: List[str] = [
    # 直播画质
    "卡顿", "掉帧", "延迟", "卡", "画面", "模糊", "不清晰",
    "画质", "花屏", "绿屏", "马赛克", "糊", "看不清",
    # 声音问题
    "声音", "听不清", "噪音", "杂音", "回声", "没声音", "静音",
    "音量", "太小", "太大", "爆音", "电流",
    # 稳定性
    "黑屏", "闪退", "崩溃", "加载", "卡死", "弹窗", "断线",
    "重连", "掉线", "进不去",
    # 主播相关
    "不说话", "无聊", "尴尬", "敷衍", "冷场", "不在",
    "骗人", "假", "坑人", "套路",
    # 商品相关
    "贵", "不值", "假货", "垃圾", "坑", "差", "烂",
    "不好", "骗", "上当", "后悔",
]

# ========== v2.0 业务预警规则配置（保留向后兼容） ==========
WARNING_RULES: Dict[str, Dict] = {
    "price": {
        "name": "价格问题",
        "keywords": ["贵", "涨价", "价格", "太贵", "不值", "坑", "割韭菜", "智商税"],
        "threshold": 3,
        "message": "价格相关负面反馈激增，建议关注定价策略",
    },
    "logistics": {
        "name": "物流问题",
        "keywords": ["发货", "物流", "快递", "没收到", "还没发", "发货慢", "几天了", "还没到", "不发货"],
        "threshold": 3,
        "message": "物流/发货相关投诉增加，建议说明发货时间和物流进度",
    },
    "aftersale": {
        "name": "售后问题",
        "keywords": ["退款", "客服", "售后", "退货", "换货", "不理人", "不回复", "投诉", "差评", "维权"],
        "threshold": 3,
        "message": "售后/客服问题频发，建议加强售后响应和客户服务",
    },
    "quality": {
        "name": "质量问题",
        "keywords": ["质量差", "质量不好", "假货", "翻车", "踩坑", "坏了", "烂", "劣质", "次品"],
        "threshold": 2,
        "message": "商品质量受到质疑，建议展示质量证明或说明产品优势",
    },
}


class WarningService:
    """
    异常预警服务 v3.0 — 四等级预警 + 负面关键词分析

    预警等级判定：
        🟢 正常 — 一切正常
        🟡 关注 — 负面率连续3分钟上涨
        🟠 预警 — 负面率超过35%
        🔴 严重 — 负面率超过50%且持续5分钟

    负面关键词分析：
        - 实时扫描弹幕中的负面关键词
        - 统计最近5分钟出现次数
        - 与5分钟前对比计算变化百分比
    """

    def __init__(self, cooldown_seconds: int = 120):
        """
        初始化预警服务

        参数:
            cooldown_seconds: 同一类预警的冷却时间（秒）
        """
        # === v2.0 保留字段 ===
        self._hit_timestamps: Dict[str, List[float]] = defaultdict(list)
        self._last_warning_time: Dict[str, float] = {}
        self._active_warnings: List[Dict] = []
        self._cooldown: int = cooldown_seconds
        self._trigger_details: Dict[str, Dict] = {}

        # === v3.0 新增：负面率追踪 ===
        # 分钟级采样：(timestamp, rate)
        self._negative_rate_samples: List[Tuple[float, float]] = []
        self._current_negative_rate: float = 0.0
        self._current_level: str = "🟢"
        self._level_text: str = "正常"

        # === v3.0 新增：负面关键词追踪 ===
        # {keyword: [(timestamp, text), ...]}
        self._keyword_hits: Dict[str, List[Tuple[float, str]]] = defaultdict(list)

    # ========== v3.0 负面率更新 ==========

    def update_negative_rate(self, rate: float, negative_count: int, total_count: int) -> None:
        """
        更新当前负面情绪率，按分钟采样并判定等级

        参数:
            rate: 当前负面率 0.0~1.0
            negative_count: 负面弹幕数
            total_count: 总弹幕数
        """
        now: float = time.time()
        self._current_negative_rate = rate

        # 每分钟采样一次（保留最后一次值）
        if self._negative_rate_samples:
            last_ts = self._negative_rate_samples[-1][0]
            if now - last_ts < 60:
                # 同一分钟内更新最后一次采样值
                self._negative_rate_samples[-1] = (last_ts, rate)
            else:
                self._negative_rate_samples.append((now, rate))
        else:
            self._negative_rate_samples.append((now, rate))

        # 清理超过10分钟的旧采样
        cutoff: float = now - 600
        self._negative_rate_samples = [
            (t, r) for t, r in self._negative_rate_samples if t >= cutoff
        ]

        # 判定等级
        self._update_level()

    def _update_level(self) -> None:
        """根据负面率趋势判定四等级预警"""
        now: float = time.time()
        rate: float = self._current_negative_rate

        if len(self._negative_rate_samples) == 0:
            self._current_level = "🟢"
            self._level_text = "正常"
            return

        # 🔴 严重：负面率超过50%且持续5分钟
        five_min_ago: float = now - 300
        recent_samples = [(t, r) for t, r in self._negative_rate_samples if t >= five_min_ago]
        if len(recent_samples) >= 4 and all(r > 0.50 for _, r in recent_samples):
            self._current_level = "🔴"
            self._level_text = "严重"
            return

        # 🟠 预警：负面率超过35%
        if rate > 0.35:
            self._current_level = "🟠"
            self._level_text = "预警"
            return

        # 🟡 关注：负面率连续3分钟上涨
        if len(self._negative_rate_samples) >= 3:
            last_3_rates = [r for _, r in self._negative_rate_samples[-3:]]
            if (last_3_rates[0] > 0 and
                last_3_rates[0] < last_3_rates[1] < last_3_rates[2]):
                self._current_level = "🟡"
                self._level_text = "关注"
                return

        # 🟢 正常
        self._current_level = "🟢"
        self._level_text = "正常"

    # ========== v3.0 负面关键词扫描 ==========

    def scan_negative_keywords(self, text: str) -> None:
        """
        扫描弹幕文本中的负面关键词

        参数:
            text: 弹幕文本内容
        """
        now: float = time.time()
        for kw in NEGATIVE_KEYWORDS:
            if kw in text:
                self._keyword_hits[kw].append((now, text))
                break  # 一条弹幕只计一个关键词，避免重复

    def get_warning_status(self) -> Dict:
        """
        获取统一预警状态 JSON（v3.0 核心接口）

        返回:
            {
                "level": "🟠",
                "level_text": "预警",
                "negative_rate": 0.42,
                "keywords": ["卡顿", "掉帧", "延迟"],         // 向后兼容
                "keywords_detail": [                           // v3.1 新增：含弹幕样本
                    {"keyword": "卡顿", "count": 8, "samples": ["卡顿严重...", "太卡了..."]},
                    ...
                ],
                "count": 128,
                "change_5min": "+62%",
                "timestamp": "14:30:00"
            }
        """
        now: float = time.time()
        five_min_ago: float = now - 300    # 最近5分钟
        ten_min_ago: float = now - 600     # 5~10分钟前

        # 统计最近5分钟关键词
        keyword_stats: Dict[str, Dict] = {}
        for kw, hits in self._keyword_hits.items():
            recent_hits = [(t, txt) for t, txt in hits if t >= five_min_ago]
            older = [t for t, _ in hits if ten_min_ago <= t < five_min_ago]
            if recent_hits:
                # 取最近3条弹幕作为样本（优先最新的）
                samples = [txt for _, txt in sorted(recent_hits, key=lambda x: x[0], reverse=True)[:3]]
                keyword_stats[kw] = {
                    "count": len(recent_hits),
                    "previous_count": len(older),
                    "samples": samples,
                }

        # 按出现次数降序排列，取前5
        sorted_keywords = sorted(
            keyword_stats.items(), key=lambda x: x[1]["count"], reverse=True
        )
        top_keywords: List[str] = [kw for kw, _ in sorted_keywords[:5]]

        # 构建带弹幕样本的关键词详情列表
        keywords_detail: List[Dict] = [
            {
                "keyword": kw,
                "count": stats["count"],
                "samples": stats["samples"],
            }
            for kw, stats in sorted_keywords[:5]
        ]

        total_count: int = sum(s["count"] for _, s in keyword_stats.items())
        previous_total: int = sum(s["previous_count"] for _, s in keyword_stats.items())

        # 计算5分钟变化百分比
        if previous_total > 0:
            change_pct: int = round((total_count - previous_total) / previous_total * 100)
            change_str = f"+{change_pct}%" if change_pct >= 0 else f"{change_pct}%"
        elif total_count > 0:
            change_str = "+100%"
        else:
            change_str = "0%"

        return {
            "level": self._current_level,
            "level_text": self._level_text,
            "negative_rate": round(self._current_negative_rate, 2),
            "keywords": top_keywords,          # 向后兼容：纯关键词列表
            "keywords_detail": keywords_detail,  # v3.1 新增：含弹幕样本
            "count": total_count,
            "change_5min": change_str,
            "timestamp": time.strftime("%H:%M:%S", time.localtime(now)),
        }

    # ========== v2.0 保留方法（向后兼容） ==========

    def scan_danmu(self, text: str, user_name: str = "") -> None:
        """
        扫描一条弹幕，检测是否命中业务预警关键词

        参数:
            text: 弹幕文本内容
            user_name: 发送弹幕的用户名
        """
        now: float = time.time()

        # v2.0 业务关键词预警
        for rule_key, rule in WARNING_RULES.items():
            for kw in rule["keywords"]:
                if kw in text:
                    self._hit_timestamps[rule_key].append(now)
                    self._trigger_details[rule_key] = {
                        "user_name": user_name,
                        "danmu_text": text,
                        "hit_keyword": kw,
                        "rule_name": rule["name"],
                        "time": time.strftime("%H:%M:%S", time.localtime(now)),
                        "timestamp": now,
                    }
                    break

        # v3.0 负面关键词扫描
        self.scan_negative_keywords(text)

    def check_warnings(self) -> List[Dict]:
        """
        检查所有规则，返回当前应触发的预警列表（v2.0 兼容）

        返回:
            [{"level": "high", "type": "price", "message": "..."}, ...]
        """
        now: float = time.time()
        window: float = 300.0
        triggered: List[Dict] = []

        for rule_key, rule in WARNING_RULES.items():
            cutoff: float = now - window
            hits: List[float] = [t for t in self._hit_timestamps.get(rule_key, []) if t >= cutoff]
            self._hit_timestamps[rule_key] = hits

            freq: int = len(hits)
            if freq >= rule["threshold"]:
                last_time: float = self._last_warning_time.get(rule_key, 0)
                if now - last_time < self._cooldown:
                    continue

                self._last_warning_time[rule_key] = now
                trigger = self._trigger_details.get(rule_key, {})
                triggered.append({
                    "level": "high",
                    "type": rule_key,
                    "type_name": rule["name"],
                    "message": rule["message"],
                    "frequency": freq,
                    "time": time.strftime("%H:%M:%S", time.localtime(now)),
                    "trigger_user": trigger.get("user_name", ""),
                    "trigger_danmu": trigger.get("danmu_text", ""),
                    "trigger_keyword": trigger.get("hit_keyword", ""),
                    "trigger_rule": rule["name"],
                    "trigger_time": trigger.get("time", ""),
                })

        if triggered:
            self._active_warnings = triggered + self._active_warnings
            self._active_warnings = self._active_warnings[:20]

        return triggered

    def get_active_warnings(self) -> List[Dict]:
        """获取当前所有活跃预警（v2.0 兼容）"""
        return self._active_warnings

    # ========== 重置 ==========

    def reset(self) -> None:
        """重置预警状态"""
        self._hit_timestamps.clear()
        self._last_warning_time.clear()
        self._active_warnings.clear()
        self._trigger_details.clear()
        # v3.0
        self._negative_rate_samples.clear()
        self._current_negative_rate = 0.0
        self._current_level = "🟢"
        self._level_text = "正常"
        self._keyword_hits.clear()
