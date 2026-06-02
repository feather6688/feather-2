# ============================================
# 运营建议服务 v3.0 — 热词驱动的智能建议
# ============================================
# 功能：
#   1. 热词匹配规则引擎：根据实时热词生成结构化运营建议
#   2. 保留 v2.0 指标驱动建议（generate 方法，向后兼容）
#   3. 新增 generate_structured 方法：返回 {topic, hotwords, advice}
#   4. 预留 AI 接口：generate_ai_advice() 后续接入 DeepSeek API
# ============================================

from typing import Dict, List, Optional


# ========== v3.0 热词→建议规则库 ==========
HOTWORD_RULES: List[Dict] = [
    {
        "topic": "用户关注商品价格",
        "hotwords": ["价格", "优惠券", "链接", "多少钱", "便宜", "贵", "涨价", "降价",
                     "优惠", "折扣", "划算", "性价比", "价钱", "原价", "现价", "福利",
                     "红包", "满减", "赠品", "送", "免费", "领", "券", "打折", "减", "返现"],
        "advice": [
            "强调限时优惠，制造紧迫感",
            "讲解产品价格优势与性价比",
            "主动引导下单，提供购买链接",
            "展示优惠券领取入口，促进转化",
        ],
    },
    {
        "topic": "用户关注商品质量",
        "hotwords": ["真假", "质量", "耐用", "正品", "靠谱", "效果", "怎么样",
                     "翻车", "踩坑", "假货", "材质", "做工", "真的好用", "不好用",
                     "质量差", "质量不好", "烂", "劣质", "次品", "保证"],
        "advice": [
            "展示质检报告或正品授权证书",
            "展示真实用户好评截图",
            "强调售后保障和退换货政策",
            "现场试用/演示产品效果",
        ],
    },
    {
        "topic": "用户关注物流发货",
        "hotwords": ["发货", "物流", "快递", "收货", "到了", "没收到", "还没发",
                     "发货慢", "包邮", "运费", "顺丰", "中通", "圆通", "几天了",
                     "还没到", "不发货", "什么时候发"],
        "advice": [
            "明确告知发货时间与物流进度",
            "展示仓储/打包实况，增强信任",
            "说明合作快递与时效保障",
            "提供订单追踪方式",
        ],
    },
    {
        "topic": "用户关注售后服务",
        "hotwords": ["客服", "售后", "退款", "退货", "换货", "投诉", "态度",
                     "不理人", "不回复", "处理", "保修", "维修", "差评", "维权"],
        "advice": [
            "主动说明售后政策与保障期限",
            "提供客服联系方式，即时响应",
            "展示已处理好评案例，消除顾虑",
            "承诺快速处理，建立信任",
        ],
    },
    {
        "topic": "用户关注直播技术问题",
        "hotwords": ["卡顿", "掉帧", "延迟", "卡", "画面", "模糊", "不清晰",
                     "声音", "听不清", "噪音", "画质", "黑屏", "闪退", "加载"],
        "advice": [
            "检查网络带宽与直播推流设置",
            "降低画质或调整编码参数",
            "向观众致歉并说明正在优化",
            "建议观众切换网络或刷新页面",
        ],
    },
    {
        "topic": "用户互动意愿低",
        "hotwords": ["无聊", "尴尬", "敷衍", "冷场", "不说话", "没意思",
                     "走了", "拜拜", "不看了", "换台", "下一个"],
        "advice": [
            "发起话题讨论或提问互动",
            "增加抽奖/秒杀/福袋活动",
            "调整直播节奏，增加内容亮点",
            "点名互动，提升参与感",
        ],
    },
]

# ========== v2.0 保留：指标驱动规则库 ==========
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
    {"id": "default_greet", "priority": "info",
     "advice": "欢迎新观众时记得点名互动，提升用户留存率"},
    {"id": "default_product", "priority": "info",
     "advice": "每5分钟口播一次主打产品，保持商品曝光节奏"},
    {"id": "default_remind", "priority": "info",
     "advice": "引导观众点赞、加粉丝团，提升直播间权重"},
]


class AdviceService:
    """
    运营建议服务 v3.0 — 热词驱动的智能建议

    v2.0 指标驱动建议（generate） → 保留向后兼容
    v3.0 热词驱动建议（generate_structured） → 新增结构化输出
    """

    def __init__(self):
        """初始化建议服务"""
        self._last_advice_ids: set[str] = set()
        self._advice_history: List[Dict] = []

    # ========== v3.0 热词驱动结构化建议 ==========

    def generate_structured(self, hotwords: List[str] = None,
                            extra_hotwords: List[str] = None) -> Dict:
        """
        根据实时热词生成结构化运营建议（v3.0 核心接口）

        参数:
            hotwords: 当前热词列表（如词云TOP词）
            extra_hotwords: 额外热词（如预警关键词）

        返回:
            {
                "topic": "用户关注商品价格",
                "hotwords": ["价格", "优惠券", "链接"],
                "advice": ["强调限时优惠", "讲解价格优势", "引导下单"]
            }
        """
        if hotwords is None:
            hotwords = []
        if extra_hotwords is None:
            extra_hotwords = []

        # 合并并去重热词
        seen: set[str] = set()
        all_words: List[str] = []
        for w in hotwords + extra_hotwords:
            if w not in seen:
                seen.add(w)
                all_words.append(w)
        if not all_words:
            # 无热词时返回默认建议
            return {
                "topic": "直播间运营建议",
                "hotwords": [],
                "advice": [
                    "保持正常直播节奏，关注弹幕反馈",
                    "适时引导点赞和加粉丝团",
                    "每5分钟口播一次主打产品",
                ],
            }

        # 匹配规则：计算每条规则的热词命中率
        best_match: Optional[Dict] = None
        best_score: int = 0
        matched_hotwords: List[str] = []

        for rule in HOTWORD_RULES:
            rule_hotwords = rule["hotwords"]
            matched = [w for w in all_words if w in rule_hotwords]
            score = len(matched)
            if score > best_score:
                best_score = score
                best_match = rule
                matched_hotwords = matched

        if best_match and best_score > 0:
            return {
                "topic": best_match["topic"],
                "hotwords": matched_hotwords[:6],  # 最多6个热词
                "advice": best_match["advice"],
            }

        # 无匹配时返回通用建议
        return {
            "topic": "直播间运营建议",
            "hotwords": all_words[:5],
            "advice": [
                "关注用户讨论热点，及时回应关切",
                "保持直播互动节奏",
                "适时推送主打产品信息",
            ],
        }

    # ========== v2.0 保留：指标驱动建议（向后兼容） ==========

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
        根据当前运营指标生成建议列表（v2.0 兼容接口）

        返回:
            建议文本列表（按优先级排序）
        """
        if sentiment_stats is None:
            sentiment_stats = {"positive": 0, "neutral": 0, "negative": 0}
        if topic_counts is None:
            topic_counts = {}
        if warnings is None:
            warnings = []

        advice_list: List[Dict] = []
        pos: int = sentiment_stats.get("positive", 0)
        neu: int = sentiment_stats.get("neutral", 0)
        neg: int = sentiment_stats.get("negative", 0)
        total: int = pos + neu + neg or 1

        neg_ratio: float = neg / total
        neu_ratio: float = neu / total

        # 规则评估
        if neg_ratio > 0.25:
            advice_list.append({"id": "neg_high", "advice": ADVICE_RULES[0]["advice"], "priority": "urgent"})
        if satisfaction < 45:
            advice_list.append({"id": "satisfaction_low", "advice": ADVICE_RULES[1]["advice"], "priority": "urgent"})
        if topic_counts.get("价格", 0) > 2:
            advice_list.append({"id": "price_focus", "advice": ADVICE_RULES[2]["advice"], "priority": "normal"})
        if topic_counts.get("发货", 0) > 2:
            advice_list.append({"id": "logistics_issue", "advice": ADVICE_RULES[3]["advice"], "priority": "normal"})
        if topic_counts.get("客服", 0) > 1:
            advice_list.append({"id": "aftersale_issue", "advice": ADVICE_RULES[4]["advice"], "priority": "urgent"})
        if heat_index < 25:
            advice_list.append({"id": "heat_low", "advice": ADVICE_RULES[5]["advice"], "priority": "normal"})
        if neu_ratio > 0.5 and total > 5:
            advice_list.append({"id": "engagement_low", "advice": ADVICE_RULES[6]["advice"], "priority": "info"})
        if pos / total > 0.5 and total > 5 and neg_ratio < 0.15:
            advice_list.append({"id": "general_positive", "advice": ADVICE_RULES[7]["advice"], "priority": "info"})

        # 默认建议
        advice_list.append({"id": "default_greet", "advice": ADVICE_RULES[8]["advice"], "priority": "info"})
        advice_list.append({"id": "default_product", "advice": ADVICE_RULES[9]["advice"], "priority": "info"})
        advice_list.append({"id": "default_remind", "advice": ADVICE_RULES[10]["advice"], "priority": "info"})

        # 根据预警生成建议
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

        # 按优先级排序并去重
        priority_order: Dict[str, int] = {"urgent": 0, "normal": 1, "info": 2}
        advice_list.sort(key=lambda x: priority_order.get(x["priority"], 99))

        seen_ids: set[str] = set()
        unique_advice: List[Dict] = []
        for item in advice_list:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                unique_advice.append(item)

        result: List[str] = [item["advice"] for item in unique_advice[:6]]
        return result

    # ========== AI 预留接口 ==========

    def generate_ai_advice(self, context: Dict) -> List[str]:
        """
        【预留接口】AI 驱动的运营建议生成
        后续接入 DeepSeek API 时使用此方法。
        """
        return []

    def reset(self) -> None:
        """重置建议状态"""
        self._last_advice_ids.clear()
        self._advice_history.clear()
