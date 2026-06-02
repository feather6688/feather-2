# 抖音直播运营智能决策分析系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.5+-4FC08D)](https://vuejs.org/)
[![ECharts](https://img.shields.io/badge/ECharts-5.5+-AA344D)](https://echarts.apache.org/)
[![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-ff69b4)]()

> 实时采集抖音直播间弹幕，WebSocket 毫秒级推送，运营指标智能分析大屏。一站式帮助运营人员掌握用户满意度、热度指数、风险等级、关注主题和异常预警。

---

## 📖 项目简介

本系统面向**直播运营人员**，通过 DrissionPage 操控浏览器实时采集抖音直播间弹幕，经 SnowNLP 情感分析 + jieba 分词 + 业务关键词聚合后，通过 WebSocket 推送到 Vue3 前端大屏，以 ECharts 可视化展示核心运营指标。

**核心能力：**
- 📊 **运营指标** — 满意度评分 / 热度指数 / 风险等级，实时计算
- 😊 **情绪分析** — 实时情绪环形图 + 累计情绪趋势图，三线面积图
- 🔥 **关注主题 TOP5** — 业务关键词聚合（价格/发货/优惠/质量/客服）
- 🚨 **异常预警中心** — 价格/物流/售后/质量 四类预警，hover 查看触发详情
- 💡 **运营建议** — 规则引擎自动生成优化建议
- 📈 **弹幕趋势** — 实时弹幕流 + 热词圆盘图 + 用户活跃排行

---

## 🏗️ 技术架构

```
                        数据采集层
     ┌──────────────────────────────────────────┐
     │  抖音直播间                                │
     │  DrissionPage 启动 Chromium               │
     │  注入 MutationObserver 监听 DOM 变化       │
     │  console.log('DANMU:...')                 │
     └──────────────────┬───────────────────────┘
                        │
                   数据处理层
     ┌──────────────────┴───────────────────────┐
     │  collector.py  弹幕采集 + 系统消息过滤      │
     │  SnowNLP 情感分析 + jieba 业务关键词提取    │
     │  services/     指标/预警/建议 四大服务     │
     │  queue.Queue   线程安全数据传递            │
     └──────────────────┬───────────────────────┘
                        │
                   通信传输层
     ┌──────────────────┴───────────────────────┐
     │  main.py  broadcast_danmu() 异步协程      │
     │  WebSocket send_json()                  │
     │  ws://127.0.0.1:8000/ws                 │
     └──────────────────┬───────────────────────┘
                        │
                   前端展示层
     ┌──────────────────┴───────────────────────┐
     │  Vue 3 App.vue  WebSocket 接收 + 状态管理 │
     │  14 个独立组件，ECharts 实时渲染           │
     └──────────────────────────────────────────┘
```

| 层级 | 技术 | 用途 |
|------|------|------|
| 数据采集 | DrissionPage + Chromium | 操控浏览器访问抖音直播间，注入 JS 监听 DOM |
| 后端框架 | FastAPI + Uvicorn | REST API + WebSocket 异步服务 |
| 中文分词 | jieba | 弹幕内容分词，业务关键词提取 |
| 情感分析 | SnowNLP | 中文自然语言情感分析，评分 + 三分类 |
| 实时通信 | WebSocket | 全双工长连接，服务端主动推送 |
| 前端框架 | Vue 3 (Composition API) | `<script setup>` 响应式数据驱动 UI |
| 构建工具 | Vite | 极速 HMR 开发服务器 |
| 图表库 | ECharts 5 | Gauge / 折线图 / 环形图 / 柱状图 |

---

## 📁 项目结构

```
douyin-live-ops-analyzer/
├── backend/                              # Python 后端
│   ├── main.py                           # FastAPI 主入口（WebSocket + 广播）
│   ├── collector.py                      # 弹幕采集 + jieba 分词 + 情绪分析
│   ├── legacy_csv_listener.py            # [参考] 原始 CSV 输出脚本
│   ├── legacy_mutation_observer.js       # [参考] 原始 MutationObserver 脚本
│   └── services/                         # 业务服务模块
│       ├── __init__.py
│       ├── sentiment_service.py          # 情绪分析服务
│       ├── metrics_service.py            # 指标服务（满意度/热度/风险/主题）
│       ├── warning_service.py            # 异常预警服务
│       └── advice_service.py             # 运营建议服务（规则引擎）
├── frontend/                             # Vue 3 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js                       # Vue 应用启动
│       ├── App.vue                       # 根组件（WebSocket + 状态 + 布局）
│       └── components/
│           ├── DanmuList.vue             # 实时弹幕滚动列表
│           ├── RealtimeSentiment.vue     # 实时情绪环形图（最近100条）
│           ├── SentimentChart.vue        # 累计情绪分析趋势图
│           ├── EmotionTrend.vue          # 实时情绪趋势（30分钟）
│           ├── WordCloud.vue             # 累计热词圆盘图
│           ├── TrendChart.vue            # 实时弹幕趋势图
│           ├── UserRank.vue              # 用户活跃排行
│           ├── SatisfactionGauge.vue     # 满意度仪表盘
│           ├── HeatCard.vue              # 热度指数卡片
│           ├── RiskCard.vue              # 风险等级卡片
│           ├── TopicTop5.vue             # 关注主题 TOP5
│           ├── AdvicePanel.vue           # 运营建议面板
│           └── WarningCenter.vue         # 异常预警中心（hover触发详情）
├── requirements.txt                      # Python 依赖
├── .gitignore                            # Git 忽略配置
└── README.md                             # 项目说明
├── .gitignore                            # Git 忽略配置
└── README.md                             # 项目说明
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Chrome 或 Edge 浏览器

### 安装

```bash
# 1. 进入项目目录
cd 抖音直播运营智能决策分析系统

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 安装前端依赖
cd frontend && npm install && cd ..
```

### 运行

一条命令启动全部服务（后端启动时自动拉起前端 Vite）：

```bash
# 在 VS Code 底部 TERMINAL（终端）面板输入，不要点右上角 ▶ Run 按钮
python backend/main.py
```

输入直播间地址后：
1. 后端自动启动 Vite 前端（无需手动 `npm run dev`）
2. DrissionPage 自动打开浏览器访问直播间
3. 直接打开 http://127.0.0.1:5173 查看大屏

| 服务 | 地址 |
|------|------|
| 前端大屏 | http://127.0.0.1:5173 |
| 后端 API | http://127.0.0.1:8000 |
| API 文档 | http://127.0.0.1:8000/docs |

---

## 🔌 WebSocket 接口

**连接地址：** `ws://127.0.0.1:8000/ws`

**消息格式（v2.0）：**

```json
{
  "type": "danmu",
  "name": "小明",
  "content": "这个价格太贵了",
  "words": ["价格", "太贵"],
  "sentiment": "negative",
  "sentiment_score": 0.21,
  "realtime_sentiment": {"positive": 45, "neutral": 30, "negative": 25},
  "global_sentiment": {"positive": 1200, "neutral": 800, "negative": 400},
  "business_words": {"价格": 2, "优惠": 1},
  "warning_hits": ["price"],
  "time": "14:25:30",
  "metrics": {
    "satisfaction": 82.0,
    "heat_index": 40.0,
    "risk_level": "中"
  },
  "topics": [
    {"name": "价格", "count": 12},
    {"name": "发货", "count": 8}
  ],
  "warnings": [{
    "level": "high", "type": "price", "type_name": "价格问题",
    "message": "价格相关负面反馈激增",
    "trigger_user": "小明", "trigger_danmu": "太贵了",
    "trigger_keyword": "太贵", "trigger_rule": "价格问题"
  }],
  "advice": ["建议强调产品性价比", "每5分钟口播一次主打产品"]
}
```

### 核心字段说明

| 字段 | 说明 |
|------|------|
| `sentiment` | 本条情绪：positive / neutral / negative |
| `sentiment_score` | SnowNLP 置信度 0~1（越高越正面） |
| `realtime_sentiment` | 最近100条弹幕的情绪分布 |
| `global_sentiment` | 开播至今累计情绪分布 |
| `metrics.satisfaction` | 满意度评分 0~100 |
| `metrics.heat_index` | 热度指数 0~100（最近1分钟弹幕量÷10×100） |
| `metrics.risk_level` | 风险等级 低/中/高 |
| `topics` | 业务关注主题 TOP5（价格/发货/优惠/质量/客服） |
| `warnings` | 异常预警（含触发用户+原始弹幕+命中关键词） |
| `advice` | 运营优化建议（规则引擎自动生成） |

---

## 📸 功能展示

> 请将实际截图放入 `screenshots/` 目录并替换下方路径。

— 整体大屏
<img width="2545" height="884" alt="image" src="https://github.com/user-attachments/assets/b9d80a80-b27c-4515-aa82-cd96aaa757b3" />
<img width="2540" height="1215" alt="image" src="https://github.com/user-attachments/assets/f80047e4-dd09-4a44-aea0-55533d6c91ad" />

运营核心指标（满意度/热度/风险）
<img width="2540" height="316" alt="image" src="https://github.com/user-attachments/assets/2cec0fc5-5a6b-44ab-9821-3b85c2d3a909" />

实时情绪 + 累计情绪分析
<img width="2536" height="705" alt="image" src="https://github.com/user-attachments/assets/4893b9d6-08bd-4a5e-a4f7-626c156af29c" />

关注主题 TOP5 + 运营建议
<img width="2540" height="289" alt="image" src="https://github.com/user-attachments/assets/390a471a-a4d6-4bc0-b5f3-9a94d88bcd73" />

异常预警中心 hover 详情
<img width="1275" height="270" alt="image" src="https://github.com/user-attachments/assets/e718cca9-e294-4bfc-a7a6-a0ef3ff16f26" />

实时弹幕列表
<img width="386" height="1210" alt="image" src="https://github.com/user-attachments/assets/db7fb277-4e83-4875-822d-bc38e80ac213" />


---

## 📄 License

MIT License — 仅供学习交流，请遵守抖音平台相关使用规定。
