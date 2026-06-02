# ============================================
# 弹幕采集模块 — DrissionPage 监听抖音直播间
# （抖音直播运营智能决策分析系统 v2.0）
# ============================================

import queue
import time
from collections import deque
from datetime import datetime
from DrissionPage import Chromium
import jieba

# SnowNLP 延迟加载（首次导入耗时长，改到首次调用时初始化）
_SNOW = None


def _get_snownlp():
    """延迟加载 SnowNLP，避免启动等待"""
    global _SNOW
    if _SNOW is None:
        from snownlp import SnowNLP as _SNLP
        _SNOW = _SNLP
    return _SNOW

# ========== 双情绪统计系统 ==========
# 累计情绪：从开播起持续累加（用于整场趋势图）
global_sentiment_stats = {"positive": 0, "neutral": 0, "negative": 0}
# 实时情绪：只保留最近 100 条弹幕（滑动窗口，用于环形图）
realtime_sentiment_queue = deque(maxlen=100)

# ========== 直播间信息 ==========
live_info = {
    "anchor_name": "",
    "live_title": ""
}


def calc_realtime_sentiment() -> dict:
    """统计最近 100 条弹幕的情绪分布"""
    result = {"positive": 0, "neutral": 0, "negative": 0}
    for label in realtime_sentiment_queue:
        result[label] += 1
    return result

# 直播场景常用词词典
for word in ['牛逼', '牛批', '卧槽', '我靠', '绝了', '无敌', '牛掰', '给力',
             '好听', '好看', '好棒', '好厉害', '太强了', '真牛', '真棒']:
    jieba.add_word(word)

# 停用词：常见虚词不参与热词统计（保留直播高频情绪词如"哈哈""666"）
STOP_WORDS = {
    # 语气助词
    '的', '了', '啊', '呢', '吧', '吗', '嘛', '哦', '嗯', '呀', '哟', '啦', '哪', '哇',
    # 代词
    '我', '你', '他', '她', '它', '们', '这', '那', '哪', '谁', '什么', '怎么', '这个', '那个', '哪个',
    # 常用虚词
    '是', '在', '有', '不', '就', '都', '也', '还', '要', '会', '能', '和', '与', '很', '好',
    '个', '一', '下', '上', '去', '来', '说', '看', '想', '让', '给', '把', '被', '对', '到',
    '没', '真', '太', '可', '多', '大', '小', '人', '可以',
}

# ============================================
# 系统消息过滤层 — 过滤所有非用户发言的系统事件
# ============================================
# 这些消息来自抖音平台自动推送，不是真实用户发言，必须丢弃
SYSTEM_MESSAGE_FILTER: list[str] = [
    # ---- 礼物 / 付费事件 ----
    "为主播加了", "加了", "送出了", "送出", "赠送", "礼物",
    # ---- 粉丝团 / 灯牌 ----
    "灯牌", "粉丝团", "加入粉丝团", "加入团", "点亮了", "成为了",
    # ---- 进入 / 关注 / 分享 / 推荐 ----
    "进入直播间", "来了", "关注了主播", "关注了", "分享了直播间", "分享了",
    "推荐了直播", "推荐直播", "推荐给",
    # ---- 等级 / 荣誉 ----
    "升级到", "荣誉等级", "升级", "等级",
    # ---- 平台公告 / 警告 ----
    "欢迎来到直播间", "严禁未成年人", "理性消费",
    "谨防网络诈骗", "切勿私下交易", "低俗色情",
    "人身伤害", "诱导消费",
    # ---- 其他系统事件 ----
    "点赞了", "点赞",
]

# 旧名兼容
SYS_KEYWORDS = SYSTEM_MESSAGE_FILTER

# MutationObserver 注入脚本（v3.1 — 新增直播间信息采集）
MONITOR_JS = '''
// ========== 直播间信息采集 ==========
// 策略：TreeWalker 深度遍历 DOM > meta 标签 > document.title（带结果校验）

// 判断文本是否为无效结果（太短、太泛、像系统词）
function isValidText(text) {
  if (!text || text.length < 2) return false;
  var invalid = ['搜索', '抖音', '直播', '抖音直播', 'Douyin', 'TikTok',
                 '推荐', '首页', '关注', '消息', '我', 'loading', 'Loading',
                 'null', 'undefined', '未知主播', '未知标题'];
  for (var i = 0; i < invalid.length; i++) {
    if (text === invalid[i]) return false;
  }
  return true;
}

// TreeWalker 遍历页面 DOM 文本节点，找最长的合理文本作为标题
function findTitleByWalk() {
  var best = '';
  // 优先在直播相关容器内遍历
  var containers = document.querySelectorAll('[class*="live-room"], [class*="LiveRoom"], [class*="room"]');
  if (containers.length === 0) {
    containers = [document.body];  // 兜底：全页遍历
  }
  for (var c = 0; c < containers.length; c++) {
    var walker = document.createTreeWalker(containers[c], NodeFilter.SHOW_TEXT, null, false);
    var node;
    while (node = walker.nextNode()) {
      var t = (node.textContent || '').trim();
      // 标题特征：4~120字符，不含过多数字/符号
      if (t.length >= 4 && t.length < 120 && !/^[\\d\\s.、，。,！!？?：:（）()\\-]+$/.test(t)) {
        if (t.length > best.length && isValidText(t)) {
          best = t;
        }
      }
    }
  }
  return best;
}

function getAnchorName() {
  // 1. TreeWalker 遍历 → 取分隔符前半
  var text = findTitleByWalk();
  if (text) {
    var parts = text.split(/[-—–|｜·•]/);
    if (parts.length >= 2) {
      var first = parts[0].trim();
      if (isValidText(first) && first.length >= 1 && first.length < 20) return first;
    }
  }

  // 2. 专用选择器
  var selList = [
    '[class*="live-room"] [class*="account"]',
    '[class*="LiveRoomInfo"] [class*="name"]',
    '[class*="webcast"] [class*="anchor"]',
    '[class*="author"]', '[class*="nick"]',
  ];
  for (var i = 0; i < selList.length; i++) {
    var el = document.querySelector(selList[i]);
    if (el && el.innerText) {
      var t2 = el.innerText.trim();
      if (isValidText(t2)) return t2;
    }
  }

  // 3. document.title 兜底
  var title = (document.title || '').replace(/\\s*[-—–|｜·•]?\\s*(抖音直播|抖音|Douyin)\\s*$/i, '').trim();
  var parts2 = title.split(/[-—–|｜·•]/);
  if (parts2.length >= 2) {
    var first2 = parts2[0].trim();
    if (isValidText(first2) && first2.length < 30) return first2;
  }
  return (isValidText(title) && title.length < 30) ? title : '未知主播';
}

function getLiveTitle() {
  // 1. TreeWalker 遍历（首选 — 直接取页面可见的标题文本）
  var text = findTitleByWalk();
  if (text) {
    // 如果包含分隔符，去掉主播名部分
    var parts = text.split(/[-—–|｜·•]/);
    if (parts.length >= 2) {
      var rest = parts.slice(1).join('-').trim();
      if (isValidText(rest) && rest.length >= 2) return rest;
    }
    if (isValidText(text)) return text;
  }

  // 2. meta 标签
  var metaSelectors = [
    'meta[property="og:title"]',
    'meta[name="description"]',
    'meta[property="og:description"]',
  ];
  for (var j = 0; j < metaSelectors.length; j++) {
    var meta = document.querySelector(metaSelectors[j]);
    if (meta && meta.content) {
      var mc = meta.content.trim();
      if (isValidText(mc) && mc.length >= 3 && mc.length < 120) return mc;
    }
  }

  // 3. document.title 兜底
  var title = (document.title || '').replace(/\\s*[-—–|｜·•]?\\s*(抖音直播|抖音|Douyin)\\s*$/i, '').trim();
  var parts2 = title.split(/[-—–|｜·•]/);
  if (parts2.length >= 2) {
    var rest2 = parts2.slice(1).join('-').trim();
    if (isValidText(rest2) && rest2.length >= 2) return rest2;
  }
  return (isValidText(title) && title.length >= 2) ? title : '未知标题';
}

// 延迟5秒后采集（页面异步渲染需要更长时间）
setTimeout(function() {
  try {
    var anchor = getAnchorName();
    var liveTitle = getLiveTitle();
    console.log('ROOMINFO_DEBUG: document.title=' + (document.title || '(empty)') +
                ' | anchor=' + anchor + ' | title=' + liveTitle);
    console.log('ROOMINFO:' + JSON.stringify({ anchor_name: anchor, live_title: liveTitle }));
  } catch(e) {
    console.log('ROOMINFO:{"anchor_name":"采集失败","live_title":"采集失败"}');
  }
}, 5000);

// ========== 弹幕监听 ==========
const targetNode = document.querySelector('[class*="webcast-chatroom___list"]');
if (!targetNode) { console.log('DANMU_SYS:target not found'); }

// 从 DOM 节点提取完整文本（含 emoji 图片的 alt 文本）
function extractFullText(node) {
  const clone = node.cloneNode(true);
  // 将所有 img 标签替换为其 alt 属性值（抖音表情的 alt 就是表情文字）
  const imgs = clone.querySelectorAll('img');
  imgs.forEach(img => {
    const alt = (img.getAttribute('alt') || '').trim();
    if (alt) {
      img.replaceWith(alt);
    }
  });
  return (clone.innerText || clone.textContent || '').trim();
}

const config = { childList: true, subtree: true };

const callback = (mutationsList) => {
  for (let mutation of mutationsList){
    if (mutation.type === "childList"){
      mutation.addedNodes.forEach((node)=>{
        if (node.nodeType === 1){
          // 往上找到弹幕项容器 webcast-chatroom__item（用户名和内容都在里面）
          var container = node;
          while (container && container.nodeType === 1) {
            var ccls = container.className || '';
            if (ccls.indexOf('webcast-chatroom__item') >= 0) break;
            container = container.parentElement;
          }
          var target = (container && container.nodeType === 1) ? container : node;
          const raw = (target.innerText || target.textContent || '').trim();
          const text = extractFullText(target);
          if (text.length > 0){
            console.log('DANMU_RAW:' + raw.replace(/\\n/g, '\\\\n'));
            console.log('DANMU:' + text);
          }
        }
      });
    }
  }
};

const observer = new MutationObserver(callback);
observer.observe(targetNode, config);
'''


def extract_words(text: str) -> list[str]:
    """使用 jieba 分词，过滤停用词和单字，返回有效词语列表"""
    words = jieba.lcut(text)
    result = []
    for w in words:
        w = w.strip()
        # 过滤：空字符串、单字、停用词、纯标点
        if len(w) < 2:
            continue
        if w in STOP_WORDS:
            continue
        result.append(w)
    return result


def is_valid_danmu(raw_text: str) -> bool:
    """
    弹幕有效性校验 — 在进入分析模块前过滤系统消息和无效内容

    校验规则：
        1. 不包含系统消息关键词（礼物、粉丝团、进入直播间等）
        2. 内容长度 ≥ 2 个字符
        3. 不是纯数字/纯标点
        4. 不是只有 emoji/特殊符号

    返回:
        True = 有效用户发言，继续分析
        False = 系统消息/无效内容，丢弃
    """
    text = raw_text.strip()

    # 规则1：长度检查（至少2个字符才有分析价值）
    if len(text) < 2:
        return False

    # 规则2：系统消息关键词过滤
    for kw in SYSTEM_MESSAGE_FILTER:
        if kw in text:
            return False

    # 规则3：过滤纯数字/纯标点消息（如 "1"、"..."、"？？"）
    stripped = text.replace(' ', '').replace('　', '')
    # 去掉常见标点
    import re
    pure_text = re.sub(r'[^\w一-鿿]', '', stripped)
    if len(pure_text) < 2:
        return False

    return True


def parse_danmu(raw_text: str) -> dict | None:
    """
    解析弹幕文本，返回 {name, content} 或 None

    注意：调用前应先用 is_valid_danmu() 过滤，本函数做二次兜底
    """
    text = raw_text.strip()

    name = ""
    content = ""

    if '：' in text:
        parts = text.split('：', 1)
        name = parts[0].strip().replace('\r', '').replace('\n', '')
        content = parts[1].strip().replace('\r', '').replace('\n', '')
    elif ':' in text:
        parts = text.split(':', 1)
        name = parts[0].strip().replace('\r', '').replace('\n', '')
        content = parts[1].strip().replace('\r', '').replace('\n', '')
    elif '\n' in text:
        # 抖音 DOM 中用户名和内容在不同 span，innerText 换行拼接
        lines = text.strip().split('\n')
        candidate_name = lines[0].strip()
        # 用户名通常较短（2~20字符）
        if len(candidate_name) >= 1 and len(candidate_name) <= 20:
            name = candidate_name
            content = ' '.join(l.strip() for l in lines[1:] if l.strip())
        else:
            content = text.replace('\r', '').replace('\n', '')
    else:
        content = text.replace('\r', '').replace('\n', '')
        # 没冒号且内容超长 → 系统公告
        if len(content) > 40:
            return None

    # 二次兜底过滤
    if not content or len(content) < 2:
        return None

    # 系统消息兜底检查
    for kw in SYSTEM_MESSAGE_FILTER:
        if kw in content:
            return None

    # 清理用户名：去掉抖音 DOM 中包裹的引号、冒号和空格
    if name:
        # 去掉首尾的引号（中英文单双引号）+ 空格 + 冒号
        # 去掉首尾空白 + 冒号 + 中英文单双引号 + 方头括号
        name = name.strip(' \t\r\n：:"“”‘’\'「」『』')
        name = name.strip(chr(0x2018))  # ‘
        name = name.strip(chr(0x2019))  # ’
        name = name.strip(chr(0x27))    # '
    if not name:
        name = "用户"

    return {"name": name, "content": content}


# ========== 情绪分析 ==========
# 基于关键词匹配的快速情绪分类（轻量级，无需 ML 模型）
POSITIVE_WORDS = {
    '棒', '厉害', '牛', '爱', '喜欢', '赞', '好听', '好看', '支持', '加油',
    '哈哈', '哈哈哈', '绝了', '给力', '无敌', '优秀', '精彩', '完美', '太棒', '牛逼',
    '牛批', '太强', '好厉害', '真牛', '真棒', '开心', '快乐', '笑死', '爱了', '帅',
    '厉害厉害', '顶', '冲', '稳', '到位', '专业', '高质量', '羡慕', '恭喜', '太牛',
    '漂亮', '不错', '666', '888', '太猛', '绝绝子', 'yyds', '好听好听',
    '棒棒', '好棒', '真好', '超棒', '强', '靠谱',
}

NEGATIVE_WORDS = {
    '差', '烂', '垃圾', '恶心', '无语', '吐了', '烦', '讨厌', '不好', '难看', '难听',
    '别播', '下播', '滚', '弱', '菜', '丢人', '什么玩意', '有毒', '别唱', '别跳',
    '唱的啥', '没意思', '无聊', '尴尬', '劣质', '噪音', '吵', '卡', '糊',
    '假唱', '没活', '取关', '太难听', '太难', '别丢人',
}


# ========== 业务关键词词库（运营决策分析用） ==========
# 按业务维度分组，用于关注主题统计和预警检测
BUSINESS_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "价格": ["价格", "多少钱", "便宜", "贵", "涨价", "降价", "优惠", "折扣", "划算", "性价比", "价钱", "原价", "现价", "不贵", "好贵"],
    "发货": ["发货", "物流", "快递", "收货", "到了", "没收到", "还没发", "发货慢", "包邮", "运费", "顺丰", "中通", "圆通", "申通", "韵达", "几天到"],
    "优惠": ["优惠", "活动", "福利", "红包", "满减", "赠品", "送", "免费", "领", "券", "优惠券", "打折", "减", "返现", "秒杀", "抢"],
    "质量": ["质量", "好用", "不好用", "耐用", "材质", "做工", "正品", "假货", "真的假的", "效果", "怎么样", "靠谱", "翻车", "踩坑", "测评"],
    "客服": ["客服", "售后", "退款", "退货", "换货", "投诉", "态度", "不理人", "回复", "处理", "保修", "维修", "差评"],
}

# 业务关键词展平集合（用于快速匹配）
BUSINESS_WORDS_FLAT: set[str] = set()
for _topic_words in BUSINESS_TOPIC_KEYWORDS.values():
    for _w in _topic_words:
        BUSINESS_WORDS_FLAT.add(_w)

# ========== 预警关键词 ==========
WARNING_KEYWORDS: dict[str, dict] = {
    "price": {
        "name": "价格问题",
        "keywords": ["贵", "涨价", "太贵", "不值", "坑", "割韭菜", "智商税"],
    },
    "logistics": {
        "name": "物流问题",
        "keywords": ["发货", "物流", "快递", "没收到", "还没发", "发货慢", "几天了", "还没到", "不发货"],
    },
    "aftersale": {
        "name": "售后问题",
        "keywords": ["退款", "客服", "售后", "退货", "换货", "不理人", "不回复", "投诉", "差评"],
    },
    "quality": {
        "name": "质量问题",
        "keywords": ["质量差", "质量不好", "假货", "翻车", "踩坑", "坏了", "劣质", "次品"],
    },
}


def extract_business_words(words: list[str]) -> dict[str, int]:
    """
    从分词结果中提取业务关键词并归类

    参数:
        words: jieba 分词产生的词语列表

    返回:
        {"价格": N, "发货": N, ...}  该条弹幕中各业务主题的命中次数
    """
    result: dict[str, int] = {}
    for w in words:
        if w in BUSINESS_WORDS_FLAT:
            # 找到所属主题
            for topic_name, topic_words in BUSINESS_TOPIC_KEYWORDS.items():
                if w in topic_words:
                    result[topic_name] = result.get(topic_name, 0) + 1
                    break
    return result


def scan_warning_keywords(text: str) -> list[str]:
    """
    扫描弹幕文本中的预警关键词

    参数:
        text: 弹幕文本内容

    返回:
        命中的预警类型列表，如 ["price", "logistics"]
    """
    hit_types: list[str] = []
    for warn_type, warn_config in WARNING_KEYWORDS.items():
        for kw in warn_config["keywords"]:
            if kw in text:
                hit_types.append(warn_type)
                break
    return hit_types


def analyze_sentiment(text: str) -> dict:
    """
    使用 SnowNLP 分析弹幕情绪

    SnowNLP 返回 0~1 的正面概率分数：
        score >= 0.6  → positive
        0.25 <= score < 0.6 → neutral（直播场景宽中性区）
        score < 0.25  → negative（只有明确负面才判定）

    参数:
        text: 弹幕文本内容

    返回:
        {"label": "positive"|"neutral"|"negative", "score": 0.0~1.0}
    """
    # 异常处理：空字符串 / None / 纯符号
    if not text or not text.strip():
        return {"label": "neutral", "score": 0.5}

    # 纯数字/纯标点直接判中性
    clean = text.strip().replace(' ', '').replace('　', '')
    if len(clean) < 2:
        return {"label": "neutral", "score": 0.5}

    try:
        S = _get_snownlp()
        score: float = S(text).sentiments  # 0~1，越高越正面
        score = round(score, 4)

        if score >= 0.6:
            label = "positive"
        elif score >= 0.25:
            label = "neutral"
        else:
            label = "negative"

        return {"label": label, "score": score}
    except Exception:
        # SnowNLP 处理异常时兜底返回中性，不中断采集流程
        return {"label": "neutral", "score": 0.5}


def run_danmu_monitor(live_url: str, danmu_queue: queue.Queue, browser_ref: list):
    """
    弹幕监听函数（后台线程入口）

    参数:
        live_url: 抖音直播间地址
        danmu_queue: 线程安全队列，用于向主线程传递弹幕
        browser_ref: 列表，用于存储 browser 引用以便清理
    """
    print(f"[监听线程] 正在启动浏览器并访问直播间...")
    print(f"[监听线程] 目标地址: {live_url}")

    try:
        browser = Chromium()
        browser_ref.append(browser)
        tab = browser.latest_tab
        tab.get(live_url)
        print("[监听线程] 正在加载直播间页面...")

        tab.console.start()
        print("[监听线程] 等待直播间聊天列表加载...")
        tab.wait.eles_loaded('x://*[contains(@class, "webcast-chatroom___list")]')
        print("[监听线程] 直播间聊天列表已加载")

        tab.run_js(MONITOR_JS)
        print("[监听线程] MutationObserver 已注入，开始监听弹幕...")

        # 在当前浏览器中新建标签页，打开前端大屏
        browser.new_tab("http://127.0.0.1:5173")
        print("[监听线程] 前端大屏已在新标签页打开")

        print("=" * 50)

        filtered_count = 0  # 过滤计数
        while True:
            msg = tab.console.wait()
            if msg is None:
                continue

            data = msg.text

            # ======== 调试日志 ========
            if data.startswith('DANMU_RAW:'):
                # 打印原始 innerText（含 \\n 标记），用于排查用户名丢失
                print(f"[DANMU_RAW] {data[10:]}")
                continue

            if data.startswith('ROOMINFO_DEBUG:'):
                print(f"[ROOMINFO_DEBUG] {data[16:]}")
                continue

            # ======== 直播间信息采集 ========
            if data.startswith('ROOMINFO:'):
                try:
                    import json
                    info = json.loads(data[9:])  # 去掉 "ROOMINFO:" 前缀
                    live_info["anchor_name"] = info.get("anchor_name", "")
                    live_info["live_title"] = info.get("live_title", "")
                    print(f"[直播间信息] 主播: {live_info['anchor_name']} | 标题: {live_info['live_title']}")
                except Exception as e:
                    print(f"[直播间信息] JSON 解析失败: {e} | 原始数据: {data}")
                continue

            if not data.startswith('DANMU:'):
                continue
            data = data[6:]  # 去掉 "DANMU:" 前缀

            # ======== 第一层过滤：系统消息 / 无效内容 ========
            if not is_valid_danmu(data):
                filtered_count += 1
                if filtered_count % 50 == 0:
                    print(f"[过滤统计] 已过滤 {filtered_count} 条系统消息/无效内容")
                continue

            parsed = parse_danmu(data)
            if parsed is None:
                filtered_count += 1
                continue

            sentiment_result = analyze_sentiment(parsed["content"])
            sentiment_label = sentiment_result["label"]
            sentiment_score = sentiment_result["score"]

            # 更新累计情绪（整场直播，持续累加）
            global_sentiment_stats[sentiment_label] += 1
            # 更新实时情绪队列（滑动窗口，只保留最近 100 条）
            realtime_sentiment_queue.append(sentiment_label)

            # 提取分词和业务关键词
            words_list = extract_words(parsed["content"])
            business_words = extract_business_words(words_list)
            warning_hits = scan_warning_keywords(parsed["content"])

            danmu_data = {
                "type": "danmu",
                "name": parsed["name"],
                "content": parsed["content"],
                "words": words_list,                         # jieba 分词（保留兼容）
                "business_words": business_words,            # 业务关键词归类
                "warning_hits": warning_hits,                # 预警关键词命中
                "sentiment": sentiment_label,                # 本条弹幕情绪（保持兼容）
                "sentiment_score": sentiment_score,          # SnowNLP 置信度 0~1
                "realtime_sentiment": calc_realtime_sentiment(),  # 实时情绪分布
                "global_sentiment": dict(global_sentiment_stats), # 累计情绪统计
                "live_info": dict(live_info),                # 直播间信息
                "timestamp": time.time(),                    # Unix 时间戳
                "time": datetime.now().strftime("%H:%M:%S")
            }

            danmu_queue.put(danmu_data)
            print(f"[弹幕 {danmu_data['time']}] {parsed['name']}: {parsed['content']} [{sentiment_label}] score={sentiment_score}")

    except Exception as e:
        print(f"[监听线程] 浏览器启动失败: {e}")
        print("[监听线程] 提示：请确保已安装 Chrome 或 Edge 浏览器")
