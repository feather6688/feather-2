# ============================================
# 运营指标服务 — 满意度评分 / 热度指数 / 风险等级
# ============================================
# 功能：
#   1. 满意度评分（0~100）：基于实时情绪分布加权计算
#   2. 热度指数（0~100）：基于最近5分钟弹幕量归一化
#   3. 风险等级：基于负面情绪占比判定
#   4. 关注主题 TOP5：基于业务关键词统计
# ============================================

import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


# ========== 业务关键词词库 ==========
# 运营关心的业务维度关键词分组
BUSINESS_KEYWORDS: Dict[str, List[str]] = {
    "价格": ["价格", "多少钱", "便宜", "贵", "涨价", "降价", "优惠", "折扣", "划算", "性价比", "价钱", "原价", "现价"],
    "发货": ["发货", "物流", "快递", "收货", "到了", "没收到", "还没发", "发货慢", "包邮", "运费", "顺丰", "中通", "圆通", "申通", "韵达"],
    "优惠": ["优惠", "活动", "福利", "红包", "满减", "赠品", "送", "免费", "领", "券", "优惠券", "打折", "减", "返现"],
    "质量": ["质量", "好用", "不好用", "耐用", "材质", "做工", "正品", "假货", "真的假的", "效果", "怎么样", "靠谱", "翻车", "踩坑"],
    "客服": ["客服", "售后", "退款", "退货", "换货", "投诉", "态度", "不理人", "回复", "处理", "保修", "维修", "差评"],
}

# 业务关键词集合（展平后用于快速匹配）
ALL_BUSINESS_WORDS: set[str] = set()
for _words in BUSINESS_KEYWORDS.values():
    for _w in _words:
        ALL_BUSINESS_WORDS.add(_w)


class MetricsService:
    """
    运营指标服务 — 从情绪统计中计算运营关键指标

    设计思路：
        - 满意度来自实时情绪分布
        - 热度来自最近5分钟弹幕量的归一化
        - 风险等级来自负面情绪占比
        - 关注主题来自业务关键词统计
    """

    def __init__(self):
        """初始化指标服务"""
        # 带时间戳的弹幕计数记录（用于计算热度）：[(timestamp, count), ...]
        self._danmu_timestamps: List[float] = []
        self._business_topic_counts: Dict[str, int] = defaultdict(int)

    # ---------- 满意度评分 ----------
    def calc_satisfaction(self, sentiment_stats: Dict[str, int]) -> float:
        """
        根据情绪分布计算用户满意度（0~100）

        公式: (positive*1.0 + neutral*0.5 - negative*1.0) / total * 100
        结果裁剪到 0~100 范围

        参数:
            sentiment_stats: {"positive": N, "neutral": N, "negative": N}

        返回:
            满意度分数 0~100
        """
        pos: int = sentiment_stats.get("positive", 0)
        neu: int = sentiment_stats.get("neutral", 0)
        neg: int = sentiment_stats.get("negative", 0)
        total: int = pos + neu + neg

        if total == 0:
            return 50.0  # 无数据时返回中性分数

        raw: float = (pos * 1.0 + neu * 0.5 - neg * 1.0) / total * 100
        # 裁剪到 0~100 范围
        score: float = max(0.0, min(100.0, raw + 50.0))
        return round(score, 1)

    # ---------- 热度指数 ----------
    def record_danmu(self) -> None:
        """记录一条弹幕的时间戳（用于热度计算）"""
        self._danmu_timestamps.append(time.time())

    def calc_heat_index(self) -> float:
        """
        计算热度指数（0~100）

        定义：最近1分钟弹幕数量 ÷ 10 × 100，上限100
            - 10条/分钟以上 → 100（满热度）
            - 5条/分钟      → 50
            - 0条           → 0

        返回:
            热度指数 0~100
        """
        now: float = time.time()
        window: float = 60.0  # 1分钟

        cutoff: float = now - window
        self._danmu_timestamps = [t for t in self._danmu_timestamps if t >= cutoff]

        count: int = len(self._danmu_timestamps)

        # 固定基准：10条/分钟 = 100热度
        heat: float = min(100.0, count / 10.0 * 100)
        return round(heat, 1)

    # ---------- 风险等级 ----------
    def calc_risk_level(self, sentiment_stats: Dict[str, int]) -> str:
        """
        根据负面情绪占比判定风险等级

        规则：
            - 负面占比 < 20%  → "低"
            - 负面占比 20~40% → "中"
            - 负面占比 > 40%   → "高"

        参数:
            sentiment_stats: {"positive": N, "neutral": N, "negative": N}

        返回:
            "低" | "中" | "高"
        """
        pos: int = sentiment_stats.get("positive", 0)
        neu: int = sentiment_stats.get("neutral", 0)
        neg: int = sentiment_stats.get("negative", 0)
        total: int = pos + neu + neg

        if total == 0:
            return "低"

        ratio: float = neg / total
        if ratio < 0.2:
            return "低"
        elif ratio < 0.4:
            return "中"
        else:
            return "高"

    # ---------- 关注主题 TOP5 ----------
    def record_business_words(self, words: List[str]) -> None:
        """
        记录弹幕中包含的业务关键词

        参数:
            words: jieba 分词产生的词语列表
        """
        for w in words:
            # 精确匹配业务关键词
            if w in ALL_BUSINESS_WORDS:
                # 找到该词所属的业务主题
                for topic_name, topic_words in BUSINESS_KEYWORDS.items():
                    if w in topic_words:
                        self._business_topic_counts[topic_name] += 1
                        break

    def get_top_topics(self, top_n: int = 5) -> List[Dict]:
        """
        获取业务关注主题 TOP N

        参数:
            top_n: 返回前 N 个主题

        返回:
            [{"name": "价格", "count": 120}, ...]
        """
        sorted_topics: List[Tuple[str, int]] = sorted(
            self._business_topic_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        result: List[Dict] = [
            {"name": name, "count": count}
            for name, count in sorted_topics[:top_n]
        ]
        # 如果不足 top_n 个，用空数据补齐
        all_topics: List[str] = list(BUSINESS_KEYWORDS.keys())
        existing: set[str] = {item["name"] for item in result}
        for topic in all_topics:
            if len(result) >= top_n:
                break
            if topic not in existing:
                result.append({"name": topic, "count": 0})
        return result

    def reset(self) -> None:
        """重置所有指标"""
        self._danmu_timestamps.clear()
        self._business_topic_counts.clear()
