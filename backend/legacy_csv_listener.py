import csv

from DrissionPage import Chromium

browser = Chromium()
tab = browser.latest_tab
tab.get(
    'https://live.douyin.com/36947836004?anchor_id=91695933082&category_name=all&is_vs=0&page_type=main_category_page&vs_ep_group_id=&vs_episode_id=&vs_episode_stage=&vs_season_id=')

# 从控制台上面去获取文本内容
tab.console.start()
# 模糊匹配 x://*[contains()]
tab.wait.eles_loaded('x://*[contains(@class, "webcast-chatroom___list")]')

# 执行监听的代码
js_code = '''
// 1. 查找页面中 class 包含 "webcast-chatroom___list" 的元素，这是直播间聊天列表容器
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
          // 8. 在控制台打印弹幕内容（加 DANMU 前缀，方便 Python 端过滤噪音）
          console.log('DANMU:' + node.innerText)
        }
      });
    }
  }
};

// 9. 创建一个 DOM 变化观察器实例，传入上面的回调函数
const observer = new MutationObserver(callback);

// 10. 启动观察器：监听目标节点，按照配置规则监听
observer.observe(targetNode, config);
'''
# 直接执行js代码
tab.run_js(js_code)

# a: 追加
# w: 会把之前的内容覆盖
# 注意：运行前请关闭 aa.csv 的 Excel 窗口，否则文件被占用会写入失败
with open('aa.csv', 'a', encoding="utf-8-sig", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['name', 'value'])
    f.flush()
    # 固定循环循环次数  用死循环
    while True:
        try:
            # 等待控制台有新的输出信息,并获取其文本内容
            msg = tab.console.wait()
            if msg is None:  # 超时无消息，继续等待
                continue
            data = msg.text
            # 过滤噪音：只处理 DANMU 前缀的弹幕消息
            if not data.startswith('DANMU:'):
                continue
            data = data[6:]  # 去掉 "DANMU:" 前缀
            print(data)

            # 按中文冒号拆分用户名和弹幕内容，一一对应写入
            if '：' in data:
                name, value = data.split('：', 1)
                name = name.strip().replace('\r', '').replace('\n', '')
                value = value.strip().replace('\r', '').replace('\n', '')

                # 跳过空内容
                if not name or not value:
                    continue
                writer.writerow([name, value])
            # 没有冒号 = 系统消息(欢迎来到直播间等)，直接跳过不写入
            f.flush()  # 每条弹幕立即写入磁盘

        except PermissionError:
            print('【警告】aa.csv 被 Excel 占用，写入失败！请关闭 Excel 后重启脚本')
        except Exception as e:
            print(f'写入异常: {e}')



