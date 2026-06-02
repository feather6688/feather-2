# 抖音直播运营智能决策分析系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.5+-4FC08D)](https://vuejs.org/)
[![ECharts](https://img.shields.io/badge/ECharts-5.5+-AA344D)](https://echarts.apache.org/)
[![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-ff69b4)]()

> v3.1 — 直播间信息采集 + 四等级预警 + 负面关键词分析 + 热词驱动智能建议  
> 实时采集抖音直播间弹幕，WebSocket 毫秒级推送，运营指标智能分析大屏。

---

## 📖 项目简介
<img width="2557" height="2102" alt="image" src="https://github.com/user-attachments/assets/2844f521-1cd2-420c-8577-5525b72bbf26" />


本系统面向**直播运营人员**，通过 DrissionPage 操控浏览器实时采集抖音直播间弹幕，经 SnowNLP 情感分析 + jieba 分词 + 业务关键词聚合后，通过 WebSocket 推送到 Vue3 前端大屏，以 ECharts 可视化展示核心运营指标。

**核心能力：**

| 模块 | 功能 | 版本 |
|------|------|------|
| 📊 运营指标 | 满意度评分 / 热度指数 / 风险等级，实时计算 | v2.0 |
| 😊 情绪分析 | 实时情绪环形图 + 累计情绪趋势图（30分钟窗口） | v2.0 |
| 🔥 关注主题 TOP5 | 业务关键词聚合（价格/发货/优惠/质量/客服） | v2.0 |
| 🚨 四等级预警 | 🟢正常 / 🟡关注 / 🟠预警 / 🔴严重，负面率追踪 | **v3.0 新增** |
| 🔍 负面关键词分析 | 直播技术类关键词（卡顿/掉帧/延迟等56个），hover 查看弹幕样本 | **v3.0 新增** |
| 💡 智能运营建议 | 热词匹配规则引擎（6大场景），结构化 JSON 输出 | **v3.0 新增** |
| 🎤 直播间信息 | 自动采集主播名称，大屏顶部实时展示 | **v3.1 新增** |
| 📈 弹幕趋势 | 实时弹幕流 + 热词圆盘图 + 用户活跃排行 | v1.0 |

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
     │  collector.py    弹幕采集 + 系统消息过滤    │
     │  SnowNLP 情感分析 + jieba 业务关键词提取    │
     │  services/       四大服务模块              │
     │    sentiment_service  情绪分析（滑动窗口）  │
     │    metrics_service    指标计算（满意度等）   │
     │    warning_service    四等级预警+关键词分析 │
     │    advice_service     热词规则引擎+建议生成 │
     │  queue.Queue     线程安全数据传递           │
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

## 🆕 v3.0 升级亮点

### 🚨 四等级预警引擎

基于负面情绪率的分钟级趋势分析，自动判定四级预警状态：

| 等级 | 触发条件 | 前端展示 |
|------|----------|----------|
| 🟢 **正常** | 默认状态 | 绿色状态条 |
| 🟡 **关注** | 负面率连续3分钟上涨 | 黄色状态条 |
| 🟠 **预警** | 负面率超过 35% | 橙色脉搏动画 |
| 🔴 **严重** | 负面率超过 50% 且持续5分钟 | 红色脉冲动画 |

### 🔍 负面关键词实时分析

- **56 个**直播场景负面关键词库（画质/声音/稳定性/主播/商品）
- 实时统计最近 5 分钟出现次数
- 与 5 分钟前对比，计算变化百分比（如 `+62%`）
- **hover 关键词标签** → 弹出弹幕样本，精准定位问题源头

### 💡 热词驱动智能建议

6 大运营场景自动匹配：

| 场景 | 匹配热词示例 | 生成建议 |
|------|-------------|----------|
| 用户关注价格 | 价格、优惠券、链接、便宜 | 强调限时优惠、讲解价格优势、引导下单 |
| 用户关注质量 | 真假、质量、耐用、翻车 | 展示质检报告、展示用户评价、强调售后 |
| 用户关注物流 | 发货、物流、快递、没收到 | 明确发货时间、展示打包实况 |
| 用户关注售后 | 客服、退款、退货、投诉 | 说明售后政策、提供客服联系方式 |
| 直播技术问题 | 卡顿、掉帧、延迟、黑屏 | 检查网络带宽、调整推流参数 |
| 互动意愿低 | 无聊、冷场、走了、换台 | 发起话题讨论、增加抽奖活动 |

### 📦 统一 JSON 输出

所有 WebSocket 消息新增两个标准化字段：

```json
{
  "warning_status": {
    "level": "🟠",
    "level_text": "预警",
    "negative_rate": 0.42,
    "keywords": ["卡顿", "掉帧", "延迟"],
    "keywords_detail": [
      {"keyword": "卡顿", "count": 8, "samples": ["太卡了看不了", "又卡顿了..."]}
    ],
    "count": 128,
    "change_5min": "+62%",
    "timestamp": "14:30:00"
  },
  "structured_advice": {
    "topic": "用户关注直播技术问题",
    "hotwords": ["卡顿", "掉帧", "延迟"],
    "advice": ["检查网络带宽与直播推流设置", "降低画质或调整编码参数"]
  }
}
```

---

## 🆕 v3.1 升级亮点

### 🎤 直播间信息自动采集

进入直播间后自动采集主播名称，展示在前端大屏顶部信息栏：

- **TreeWalker DOM 深度遍历** — 自动识别页面中的主播名称和直播标题
- **多级降级策略** — DOM 选择器 → meta 标签 → document.title
- **`isValidText()` 校验** — 过滤"搜索/抖音/直播/loading"等无效值
- **延迟 5 秒采集** — 等待页面异步渲染完成

### 🔧 弹幕用户名精准提取

修复了抖音 DOM 中用户名和内容分属不同 `<span>` 导致用户名丢失的问题：

- **容器爬升** — MutationObserver 从深层 `<span>` 向上爬升到 `webcast-chatroom__item` 容器
- **多格式兼容** — 支持 `：` 全角冒号、`:` 半角冒号、`\n` 换行三种分隔
- **引号清洗** — 自动去除抖音 DOM 包裹的 `""` 中文引号和 `"` ASCII 引号
- **调试日志** — `[DANMU_RAW]` 实时输出原始 DOM 文本，便于排查

### 📦 新增 WebSocket 字段

```json
{
  "live_info": {
    "anchor_name": "浮乱迷生",
    "live_title": "今天给大家带来..."
  }
}
```

---

## 📁 项目结构

```
douyin-live-ops-analyzer/
├── backend/                              # Python 后端
│   ├── main.py                           # FastAPI 主入口（WebSocket + 广播协程）
│   ├── collector.py                      # 弹幕采集 + jieba 分词 + 情绪分析
│   ├── danmu_collector.js                # 浏览器注入的弹幕监听 JS
│   └── services/                         # 业务服务模块
│       ├── __init__.py
│       ├── sentiment_service.py          # SnowNLP 情绪分析（滑动窗口）
│       ├── metrics_service.py            # 满意度/热度/风险/TOP5 主题
│       ├── warning_service.py            # 🔥 四等级预警 + 负面关键词分析
│       └── advice_service.py             # 🔥 热词规则引擎 + 结构化建议
├── frontend/                             # Vue 3 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js                       # Vue 应用启动
│       ├── App.vue                       # 根组件（WebSocket + 状态管理 + 大屏布局）
│       └── components/
│           ├── DanmuList.vue             # 实时弹幕滚动列表
│           ├── RealtimeSentiment.vue     # 实时情绪环形图
│           ├── SentimentChart.vue        # 累计情绪趋势图
│           ├── EmotionTrend.vue          # 30分钟情绪时间线
│           ├── WordCloud.vue             # 热词圆盘图
│           ├── TrendChart.vue            # 弹幕量趋势图
│           ├── UserRank.vue              # 用户活跃排行
│           ├── SatisfactionGauge.vue     # 满意度仪表盘
│           ├── HeatCard.vue              # 热度指数卡片
│           ├── RiskCard.vue              # 风险等级卡片
│           ├── TopicTop5.vue             # 关注主题 TOP5 柱状图
│           ├── AdvicePanel.vue           # 🔥 结构化建议面板
│           └── WarningCenter.vue         # 🔥 四等级预警中心（hover详情）
├── requirements.txt                      # Python 依赖
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

### 消息格式（v3.0）

```json
{
  // ===== v1.0 基础字段 =====
  "type": "danmu",
  "name": "小明",
  "content": "这个价格太贵了",
  "words": ["价格", "太贵"],
  "sentiment": "negative",
  "sentiment_score": 0.21,
  "realtime_sentiment": {"positive": 45, "neutral": 30, "negative": 25},
  "global_sentiment": {"positive": 1200, "neutral": 800, "negative": 400},
  "time": "14:25:30",

  // ===== v2.0 运营指标 =====
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
    "trigger_keyword": "太贵"
  }],
  "advice": ["建议强调产品性价比", "每5分钟口播一次主打产品"],

  // ===== v3.0 统一预警 + 智能建议 =====
  "warning_status": {
    "level": "🟠",
    "level_text": "预警",
    "negative_rate": 0.42,
    "keywords": ["卡顿", "掉帧", "延迟"],
    "keywords_detail": [
      {"keyword": "卡顿", "count": 8, "samples": ["太卡了看不了", "又卡顿无语"]}
    ],
    "count": 128,
    "change_5min": "+62%",
    "timestamp": "14:30:00"
  },
  "structured_advice": {
    "topic": "用户关注价格",
    "hotwords": ["价格", "优惠券", "链接"],
    "advice": ["强调限时优惠", "讲解价格优势", "引导下单"]
  }
}
```

### 核心字段说明

| 字段 | 说明 | 版本 |
|------|------|------|
| `sentiment` | 本条情绪：positive / neutral / negative | v1.0 |
| `realtime_sentiment` | 最近 100 条弹幕的情绪分布 | v1.0 |
| `metrics.satisfaction` | 满意度评分 0~100 | v2.0 |
| `metrics.heat_index` | 热度指数 0~100 | v2.0 |
| `metrics.risk_level` | 风险等级 低/中/高 | v2.0 |
| `topics` | 关注主题 TOP5 | v2.0 |
| `warnings` | 业务预警列表（含触发用户+原始弹幕） | v2.0 |
| `advice` | 指标驱动建议（文字列表） | v2.0 |
| `warning_status` | 🔥 四等级预警 + 负面关键词 + 弹幕样本 | **v3.0** |
| `structured_advice` | 🔥 热词匹配场景 + 结构化建议 JSON | **v3.0** |

### 定期推送消息

当没有新弹幕时，后端每 5 秒推送一次快照：

```json
{
  "type": "metrics_snapshot",
  "metrics": {"satisfaction": 82.0, "heat_index": 40.0, "risk_level": "低"},
  "sentiment_timeline": {
    "timeline": ["14:00:00", "14:00:30", ...],
    "positive": [12, 15, ...],
    "neutral": [8, 7, ...],
    "negative": [3, 4, ...]
  },
  "warnings": [...],
  "warning_status": {...},
  "realtime_sentiment": {"positive": 45, "neutral": 30, "negative": 25}
}
```

---

## 🧩 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 健康检查 + 系统状态 + v3.0 预警/建议数据 |
| GET | `/api/metrics` | 运营指标 + 关注主题 + 预警 + 建议完整快照 |

---

## 📸 功能展示

— 整体大屏
<img width="2557" height="2102" alt="image" src="https://github.com/user-attachments/assets/613e6f8f-74a0-4240-91f2-6953d994e0dd" />

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
