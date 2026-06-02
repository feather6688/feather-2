// 1. 查找页面中 class 包含 "webcast-chatroom___list" 的元素，这是直播间聊天列表容器  网页源码
const targetNode = document.querySelector('[class*="webcast-chatroom___list"]');

// 2. 配置 MutationObserver 要监听哪些类型的 DOM 变化
const config = {
  attributes: true,   // 监听元素属性（class/style 等）的变化
  childList: true,    // 监听子节点的新增/删除（聊天消息就是新增子节点）
  subtree: true       // 监听所有后代节点（不只是直接子节点）
};

// 3. 定义当 DOM 发生变化时，自动执行的回调函数
// mutationsList 是浏览器自动传过来的：所有变化记录的数组
const callback = (mutationsList)=> {
  //  mutationsList: 一堆, 数组类型 [div, div, div, div, div]
  // 4. 遍历每一条 DOM 变化记录
  for (let mutation of mutationsList){
    // 5. 只处理【子节点新增/删除】这种变化（排除属性变化）
    if (mutation.type === "childList"){
      // 6. 遍历本次变化中【新增】的所有节点
      mutation.addedNodes.forEach((node)=>{
        // 7. 过滤：只处理 DIV 元素节点（nodeType=1 代表元素节点）
        if (node.tagName === "DIV" && node.nodeType===1){
          // 8. 在控制台打印这个新增 DIV 里的文本内容（就是直播间消息）
          console.log(node.innerText)
        }
      });
    }
  }
};

// 9. 创建一个 DOM 变化观察器实例，传入上面的回调函数
const observer = new MutationObserver(callback);

// 10. 启动观察器：监听目标节点，按照配置规则监听
observer.observe(targetNode, config);


