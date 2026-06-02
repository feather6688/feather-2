# ============================================
# 运营建议服务 — 基于规则引擎的运营优化建议
# ============================================
# 功能：
#   1. 规则引擎：根据情绪/指标/预警生成运营建议
#   2. 预留 AI 接口：generate_ai_advice() 后续接入 DeepSeek API
#   3. 建议分级：紧急 / 一般 / 优化
# ============================================

from typing import Dict, List, Optional


# ========== 运营建议规则库 ==========
ADVICE_RULES: List[Dict] = [
    {"id": "neg_high", "priority": "urgent",
     "advice": "负面反馈增加，建议主播及时回应用户关切，主动沟通化解不满"},
    {"id": "satisfaction_low", "priority": "urgent",
     "advice": "用户满意度下降，建议增加互动环节、提升直播内容质量"},
    {"id": "price_focus", "priority": "normal",
     "advice": "用户高度关注价格，建议强调产品性价比和当前优惠活动力度"},
    {"id": "logistics_issue", "priority": "normal",
     "advice": "物流相关咨询增多，建议明确告知发货时间、展示物流进度"},
    {"id": "aftersale_issue", "priority": "urgent",
     "advice": "售后投诉增多，建议主动说明售后政策、提供客服联系方式"},
    {"id": "heat_low", "priority": "normal",
     "advice": "当前热度较低，建议增加互动/抽奖/秒杀等促活手段"},
    {"id": "engagement_low", "priority": "info",
     "advice": "观众互动偏少，建议发起话题讨论、提问互动提升参与感"},
    {"id": "general_positive", "priority": "info",
     "advice": "直播间氛围良好，可以趁机引导下单、宣传主打产品"},
    # === 新增：默认建议（始终显示） ===
    {"id": "default_greet", "priority": "info",
     "advice": "欢迎新观众时记得点名互动，提升用户留存率"},
    {"id": "default_product", "priority": "info",
     "advice": "每5分钟口播一次主打产品，保持商品曝光节奏"},
    {"id": "default_remind", "priority": "info",
     "advice": "引导观众点赞、加粉丝团，提升直播间权重"},
]


class AdviceService:
    """
    运营建议服务 — 根据实时数据生成运营优化建议

    当前使用规则引擎，后续可接入 DeepSeek API 实现 AI 建议。
    """

    def __init__(self):
        """初始化建议服务"""
        # 已生成的建议缓存（按规则ID去重）
        self._last_advice_ids: set[str] = set()
        self._advice_history: List[Dict] = []

    def generate(
        self,
        sentiment_stats: Optional[Dict[str, int]] = None,
        satisfaction: float = 50.0,
        heat_index: float = 50.0,
        risk_level: str = "低",
        topic_counts: Optional[Dict[str, int]] = None,
        warnings: Optional[List[Dict]] = None,
    ) -> List[str]:
        """
        根据当前运营指标生成建议列表

        参数:
            sentiment_stats: 情绪分布 {"positive": N, "neutral": N, "negative": N}
            satisfaction: 满意度评分 0~100
            heat_index: 热度指数 0~100
            risk_level: 风险等级 "低"|"中"|"高"
            topic_counts: 业务主题计数 {"价格": N, "发货": N, ...}
            warnings: 当前预警列表

        返回:
            建议文本列表（按优先级排序）
        """
        if sentiment_stats is None:
            sentiment_stats = {"positive": 0, "neutral": 0, "negative": 0}
        if topic_counts is None:
            topic_counts = {}
        if warnings is None:
            warnings = []

        advice_list: List[Dict] = []  # [{id, advice, priority}, ...]
        pos: int = sentiment_stats.get("positive", 0)
        neu: int = sentiment_stats.get("neutral", 0)
        neg: int = sentiment_stats.get("negative", 0)
        total: int = pos + neu + neg or 1

        neg_ratio: float = neg / total
        neu_ratio: float = neu / total

        # ----- 规则评估（降低阈值，让建议更灵敏） -----

        # 1. 负面情绪占比过高 >25%（原30%）
        if neg_ratio > 0.25:
            advice_list.append({"id": "neg_high", "advice": ADVICE_RULES[0]["advice"], "priority": "urgent"})

        # 2. 满意度偏低 <45（原40）
        if satisfaction < 45:
            advice_list.append({"id": "satisfaction_low", "advice": ADVICE_RULES[1]["advice"], "priority": "urgent"})

        # 3. 价格关注度高 >2条（原5）
        if topic_counts.get("价格", 0) > 2:
            advice_list.append({"id": "price_focus", "advice": ADVICE_RULES[2]["advice"], "priority": "normal"})

        # 4. 物流问题 >2条（原5）
        if topic_counts.get("发货", 0) > 2:
            advice_list.append({"id": "logistics_issue", "advice": ADVICE_RULES[3]["advice"], "priority": "normal"})

        # 5. 售后问题 >1条（原3）
        if topic_counts.get("客服", 0) > 1:
            advice_list.append({"id": "aftersale_issue", "advice": ADVICE_RULES[4]["advice"], "priority": "urgent"})

        # 6. 热度偏低 <25（原20）
        if heat_index < 25:
            advice_list.append({"id": "heat_low", "advice": ADVICE_RULES[5]["advice"], "priority": "normal"})

        # 7. 中性占比高，互动不足 >50% + 弹幕>5（原60%+10）
        if neu_ratio > 0.5 and total > 5:
            advice_list.append({"id": "engagement_low", "advice": ADVICE_RULES[6]["advice"], "priority": "info"})

        # 8. 整体良好 正面>50% + 弹幕>5 + 负面<15%
        if pos / total > 0.5 and total > 5 and neg_ratio < 0.15:
            advice_list.append({"id": "general_positive", "advice": ADVICE_RULES[7]["advice"], "priority": "info"})

        # 9. 始终输出的默认运营建议
        advice_list.append({"id": "default_greet", "advice": ADVICE_RULES[8]["advice"], "priority": "info"})
        advice_list.append({"id": "default_product", "advice": ADVICE_RULES[9]["advice"], "priority": "info"})
        advice_list.append({"id": "default_remind", "advice": ADVICE_RULES[10]["advice"], "priority": "info"})

        # 10. 根据预警生成建议
        for w in warnings:
            w_type: str = w.get("type", "")
            if w_type == "price":
                advice_list.append({
                    "id": f"warn_price_{w.get('time', '')}",
                    "advice": "⚠️ 价格负面反馈激增，建议立即了解用户价格疑虑并作出解释",
                    "priority": "urgent",
                })
            elif w_type == "logistics":
                advice_list.append({
                    "id": f"warn_logistics_{w.get('time', '')}",
                    "advice": "⚠️ 物流投诉增多，建议立即说明发货安排并安抚用户情绪",
                    "priority": "urgent",
                })
            elif w_type == "aftersale":
                advice_list.append({
                    "id": f"warn_aftersale_{w.get('time', '')}",
                    "advice": "⚠️ 售后问题频发，建议安排客服及时处理，避免差评扩散",
                    "priority": "urgent",
                })
            elif w_type == "quality":
                advice_list.append({
                    "id": f"warn_quality_{w.get('time', '')}",
                    "advice": "⚠️ 质量质疑增多，建议展示产品实物、检测报告，消除疑虑",
                    "priority": "urgent",
                })

        # ----- 按优先级排序并去重 -----
        priority_order: Dict[str, int] = {"urgent": 0, "normal": 1, "info": 2}
        advice_list.sort(key=lambda x: priority_order.get(x["priority"], 99))

        # 去重（同一规则ID只保留一次）
        seen_ids: set[str] = set()
        unique_advice: List[Dict] = []
        for item in advice_list:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                unique_advice.append(item)

        # 只返回建议文本（最多6条）
        result: List[str] = [item["advice"] for item in unique_advice[:6]]
        return result

    def generate_ai_advice(
        self,
        context: Dict,
    ) -> List[str]:
        """
        【预留接口】AI 驱动的运营建议生成

        后续接入 DeepSeek API 时使用此方法。
        当前返回空列表。

        参数:
            context: 包含情绪、指标、预警、弹幕样本等完整上下文

        返回:
            AI 生成的建议文本列表
        """
        # TODO: 接入 DeepSeek API
        # import requests
        # response = requests.post(
        #     "https://api.deepseek.com/v1/chat/completions",
        #     headers={"Authorization": "Bearer <API_KEY>"},
        #     json={
        #         "model": "deepseek-chat",
        #         "messages": [
        #             {"role": "system", "content": "你是直播运营分析专家..."},
        #             {"role": "user", "content": f"根据以下数据给出运营建议：{context}"}
        #         ]
        #     }
        # )
        # return parse_advice(response.json())
        return []

    def reset(self) -> None:
        """重置建议状态"""
        self._last_advice_ids.clear()
        self._advice_history.clear()
