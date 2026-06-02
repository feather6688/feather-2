// ============================================
// 抖音直播间弹幕采集脚本 v3.1
// 功能：
//   1. 监听弹幕（DANMU:）
//   2. 采集主播名称 + 直播标题（ROOMINFO:）
// 策略：TreeWalker 深度遍历 DOM > meta 标签 > document.title（带结果校验）
// ============================================

// ========== 直播间信息采集 ==========

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
  var containers = document.querySelectorAll('[class*="live-room"], [class*="LiveRoom"], [class*="room"]');
  if (containers.length === 0) {
    containers = [document.body];
  }
  for (var c = 0; c < containers.length; c++) {
    var walker = document.createTreeWalker(containers[c], NodeFilter.SHOW_TEXT, null, false);
    var node;
    while (node = walker.nextNode()) {
      var t = (node.textContent || '').trim();
      if (t.length >= 4 && t.length < 120 && !/^[\d\s.、，。,！!？?：:（）()\-]+$/.test(t)) {
        if (t.length > best.length && isValidText(t)) {
          best = t;
        }
      }
    }
  }
  return best;
}

function getAnchorName() {
  var text = findTitleByWalk();
  if (text) {
    var parts = text.split(/[-—–|｜·•]/);
    if (parts.length >= 2) {
      var first = parts[0].trim();
      if (isValidText(first) && first.length >= 1 && first.length < 20) return first;
    }
  }
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
  var title = (document.title || '').replace(/\s*[-—–|｜·•]?\s*(抖音直播|抖音|Douyin)\s*$/i, '').trim();
  var parts2 = title.split(/[-—–|｜·•]/);
  if (parts2.length >= 2) {
    var first2 = parts2[0].trim();
    if (isValidText(first2) && first2.length < 30) return first2;
  }
  return (isValidText(title) && title.length < 30) ? title : '未知主播';
}

function getLiveTitle() {
  var text = findTitleByWalk();
  if (text) {
    var parts = text.split(/[-—–|｜·•]/);
    if (parts.length >= 2) {
      var rest = parts.slice(1).join('-').trim();
      if (isValidText(rest) && rest.length >= 2) return rest;
    }
    if (isValidText(text)) return text;
  }
  var metaSel = ['meta[property="og:title"]', 'meta[name="description"]', 'meta[property="og:description"]'];
  for (var j = 0; j < metaSel.length; j++) {
    var meta = document.querySelector(metaSel[j]);
    if (meta && meta.content) {
      var mc = meta.content.trim();
      if (isValidText(mc) && mc.length >= 3 && mc.length < 120) return mc;
    }
  }
  var title = (document.title || '').replace(/\s*[-—–|｜·•]?\s*(抖音直播|抖音|Douyin)\s*$/i, '').trim();
  var parts2 = title.split(/[-—–|｜·•]/);
  if (parts2.length >= 2) {
    var rest2 = parts2.slice(1).join('-').trim();
    if (isValidText(rest2) && rest2.length >= 2) return rest2;
  }
  return (isValidText(title) && title.length >= 2) ? title : '未知标题';
}

// 延迟5秒采集
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

const config = {
  attributes: true,
  childList: true,
  subtree: true
};

const callback = (mutationsList)=> {
  for (let mutation of mutationsList){
    if (mutation.type === "childList"){
      mutation.addedNodes.forEach((node)=>{
        if (node.tagName === "DIV" && node.nodeType===1){
          console.log(node.innerText)
        }
      });
    }
  }
};

const observer = new MutationObserver(callback);
observer.observe(targetNode, config);
