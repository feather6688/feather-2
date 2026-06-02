# ============================================
# 异常预警服务 — 实时检测运营风险并触发预警
# ============================================
# 功能：
#   1. 按业务维度统计最近5分钟负面/问题反馈频率
#   2. 达到阈值时生成预警消息
#   3. 支持多预警同时存在
#   4. 支持预警冷却机制（避免重复发送）
# ============================================

import time
from collections import defaultdict
from typing import Dict, List, Optional


# ========== 预警规则配置 ==========
WARNING_RULES: Dict[str, Dict] = {
    "price": {
        "name": "价格问题",
        "keywords": ["贵", "涨价", "价格", "太贵", "不值", "坑", "割韭菜", "智商税"],
        "threshold": 3,      # 5分钟内出现3次触发
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
    异常预警服务 — 检测运营过程中的风险信号

    预警流程：
        1. 收到弹幕时扫描预警关键词
        2. 按规则分组统计最近5分钟命中频率
        3. 达到阈值时生成预警（带冷却机制）
    """

    def __init__(self, cooldown_seconds: int = 120):
        """
        初始化预警服务

        参数:
            cooldown_seconds: 同一类预警的冷却时间（秒），避免重复推送
        """
        # 每条规则的命中的时间戳列表：{rule_key: [timestamp, ...]}
        self._hit_timestamps: Dict[str, List[float]] = defaultdict(list)
        # 每条规则上次触发预警的时间
        self._last_warning_time: Dict[str, float] = {}
        # 当前活跃的预警列表
        self._active_warnings: List[Dict] = []
        # 冷却时间
        self._cooldown: int = cooldown_seconds
        # 【新增】触发详情：{rule_key: {user_name, danmu_text, hit_keyword, time}}
        self._trigger_details: Dict[str, Dict] = {}

    def scan_danmu(self, text: str, user_name: str = "") -> None:
        """
        扫描一条弹幕，检测是否命中预警关键词，同时记录触发详情

        参数:
            text: 弹幕文本内容
            user_name: 发送弹幕的用户名
        """
        now: float = time.time()

        for rule_key, rule in WARNING_RULES.items():
            for kw in rule["keywords"]:
                if kw in text:
                    self._hit_timestamps[rule_key].append(now)
                    # 记录触发详情（保留最新一条）
                    self._trigger_details[rule_key] = {
                        "user_name": user_name,
                        "danmu_text": text,
                        "hit_keyword": kw,
                        "rule_name": rule["name"],
                        "time": time.strftime("%H:%M:%S", time.localtime(now)),
                        "timestamp": now,
                    }
                    break  # 一条弹幕对同一规则只计一次

    def check_warnings(self) -> List[Dict]:
        """
        检查所有规则，返回当前应触发的预警列表

        返回:
            [{"level": "high", "type": "price", "message": "..."}, ...]
        """
        now: float = time.time()
        window: float = 300.0  # 5分钟窗口
        triggered: List[Dict] = []

        for rule_key, rule in WARNING_RULES.items():
            # 清理过期时间戳
            cutoff: float = now - window
            hits: List[float] = [t for t in self._hit_timestamps.get(rule_key, []) if t >= cutoff]
            self._hit_timestamps[rule_key] = hits

            freq: int = len(hits)

            # 检查是否达到阈值
            if freq >= rule["threshold"]:
                # 检查冷却
                last_time: float = self._last_warning_time.get(rule_key, 0)
                if now - last_time < self._cooldown:
                    # 在冷却期内，沿用上次的预警消息（只追加不重复）
                    continue

                self._last_warning_time[rule_key] = now
                # 获取触发详情
                trigger = self._trigger_details.get(rule_key, {})
                triggered.append({
                    "level": "high",
                    "type": rule_key,
                    "type_name": rule["name"],
                    "message": rule["message"],
                    "frequency": freq,
                    "time": time.strftime("%H:%M:%S", time.localtime(now)),
                    # 【新增】触发详情 — 供前端悬停查看
                    "trigger_user": trigger.get("user_name", ""),
                    "trigger_danmu": trigger.get("danmu_text", ""),
                    "trigger_keyword": trigger.get("hit_keyword", ""),
                    "trigger_rule": rule["name"],
                    "trigger_time": trigger.get("time", ""),
                })

        # 更新活跃预警列表
        if triggered:
            self._active_warnings = triggered + self._active_warnings
            # 最多保留 20 条历史预警
            self._active_warnings = self._active_warnings[:20]

        return triggered

    def get_active_warnings(self) -> List[Dict]:
        """获取当前所有活跃预警（含历史）"""
        return self._active_warnings

    def reset(self) -> None:
        """重置预警状态"""
        self._hit_timestamps.clear()
        self._last_warning_time.clear()
        self._active_warnings.clear()
