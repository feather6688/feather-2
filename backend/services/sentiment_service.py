# ============================================
# 情绪分析服务 — 基于 SnowNLP 的真实情感分析
# ============================================
# 功能：
#   1. 弹幕文本情绪分类（positive / negative / neutral）
#   2. 累计情绪统计 + 滑动窗口实时情绪
#   3. 返回置信度分数（sentiment_score）
#
# v2.1: 从关键词匹配升级为 SnowNLP 自然语言情感分析
# ============================================

from collections import deque
from typing import Dict

# SnowNLP 延迟加载（避免启动时等待）
_SNOW = None
_HAS_SNOWNLP = True  # 默认有，首次调用时再校验


def _get_snownlp():
    """延迟加载 SnowNLP"""
    global _SNOW, _HAS_SNOWNLP
    if _SNOW is None:
        try:
            from snownlp import SnowNLP as _S
            _SNOW = _S
        except ImportError:
            _HAS_SNOWNLP = False
            _SNOW = False
    return _SNOW if _SNOW is not False else None


class SentimentService:
    """情绪分析服务 — 基于 SnowNLP 的中文情感分析"""

    def __init__(self, window_size: int = 100):
        """
        初始化情绪分析服务

        参数:
            window_size: 滑动窗口大小（最近 N 条弹幕）
        """
        self.global_stats: Dict[str, int] = {"positive": 0, "neutral": 0, "negative": 0}
        self._window_size: int = window_size
        self._realtime_queue: deque[str] = deque(maxlen=window_size)

    @staticmethod
    def analyze(text: str) -> str:
        """
        分析单条弹幕文本的情绪倾向（基于 SnowNLP）

        参数:
            text: 弹幕文本内容

        返回:
            "positive" | "negative" | "neutral"
        """
        S = _get_snownlp()
        if S is None:
            return "neutral"

        if not text or not text.strip():
            return "neutral"
        clean = text.strip().replace(' ', '').replace('　', '')
        if len(clean) < 2:
            return "neutral"

        try:
            score: float = S(text).sentiments
            if score >= 0.6:
                return "positive"
            elif score >= 0.25:
                return "neutral"
            else:
                return "negative"
        except Exception:
            return "neutral"

    @staticmethod
    def analyze_with_score(text: str) -> Dict:
        """
        分析情绪并返回置信度分数

        返回:
            {"label": "positive"|"neutral"|"negative", "score": 0.0~1.0}
        """
        S = _get_snownlp()
        if S is None:
            return {"label": "neutral", "score": 0.5}

        if not text or not text.strip():
            return {"label": "neutral", "score": 0.5}
        clean = text.strip().replace(' ', '').replace('　', '')
        if len(clean) < 2:
            return {"label": "neutral", "score": 0.5}

        try:
            score: float = round(S(text).sentiments, 4)
            if score >= 0.6:
                label = "positive"
            elif score >= 0.25:
                label = "neutral"
            else:
                label = "negative"
            return {"label": label, "score": score}
        except Exception:
            return {"label": "neutral", "score": 0.5}

    def record(self, text: str) -> str:
        """
        记录一条弹幕并返回其情绪标签

        参数:
            text: 弹幕文本内容

        返回:
            "positive" | "negative" | "neutral"
        """
        label: str = self.analyze(text)
        self.global_stats[label] += 1
        self._realtime_queue.append(label)
        return label

    def get_realtime(self) -> Dict[str, int]:
        """获取最近 N 条弹幕的情绪分布（滑动窗口）"""
        result: Dict[str, int] = {"positive": 0, "neutral": 0, "negative": 0}
        for label in self._realtime_queue:
            result[label] += 1
        return result

    def get_global(self) -> Dict[str, int]:
        """获取开播以来累计情绪统计"""
        return dict(self.global_stats)

    def reset(self) -> None:
        """重置所有统计（用于新直播场次）"""
        self.global_stats = {"positive": 0, "neutral": 0, "negative": 0}
        self._realtime_queue.clear()
