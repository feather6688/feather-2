<!--
============================================
App.vue — 抖音直播运营智能决策分析系统 根组件 v3.0
负责：WebSocket连接 + 数据处理 + 运营决策大屏布局

升级变更（v1.0 → v3.0）：
  - 新增运营指标面板（满意度 / 热度 / 风险等级）
  - 新增加关注主题 TOP5
  - 新增 运营建议面板
  - 新增异常预警中心
  - 新增情绪趋势图（30分钟窗口）
  - 保留所有 v1.0 原有功能组件
============================================
-->
<template>
  <div class="dashboard">

    <!-- ========== 顶部标题栏 ========== -->
    <header class="header">
      <div class="header-left">
        <span class="logo-icon">&#9654;</span>
        <h1 class="title">抖音直播运营智能决策分析系统</h1>
        <span class="version-tag">v3.1</span>
      </div>
      <div class="header-right">
        <div class="status-badge" :class="{ connected: wsConnected }">
          <span class="status-dot"></span>
          <span>{{ wsConnected ? 'WebSocket 已连接' : 'WebSocket 未连接' }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">累计弹幕</span>
          <span class="stat-value">{{ danmuList.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">累计用户</span>
          <span class="stat-value">{{ uniqueUsers }}</span>
        </div>
      </div>
    </header>

    <!-- ========== v3.1 直播间信息栏 ========== -->
    <div class="live-info-bar" v-if="liveInfo.anchor_name">
      <div class="live-info-item">
        <span class="live-info-icon">🎤</span>
        <span class="live-info-label">主播</span>
        <span class="live-info-value" :title="liveInfo.anchor_name">{{ liveInfo.anchor_name || '加载中...' }}</span>
      </div>
    </div>

    <!-- ========== 第一行：运营核心指标（满意度 / 热度 / 风险） ========== -->
    <section class="metrics-row">
      <div class="panel metric-panel">
        <SatisfactionGauge :value="metrics.satisfaction" />
      </div>
      <div class="panel metric-panel">
        <HeatCard :value="metrics.heat_index" />
      </div>
      <div class="panel metric-panel">
        <RiskCard :level="metrics.risk_level" />
      </div>
    </section>

    <!-- ========== 第二行：关注主题 TOP5 + 运营建议 ========== -->
    <section class="topics-advice-row">
      <div class="panel topics-panel">
        <TopicTop5 :topics="topics" />
      </div>
      <div class="panel advice-panel-wrap">
        <AdvicePanel :list="advice" :adviceJson="structuredAdvice" />
      </div>
    </section>

    <!-- ========== 第三行：情绪趋势 + 异常预警（并排） ========== -->
    <section class="trend-warn-row">
      <div class="panel trend-warn-panel">
        <EmotionTrend :timeline="sentimentTimeline" />
      </div>
      <div class="panel trend-warn-panel">
        <WarningCenter :warnings="warnings" :wstatus="warningStatus" />
      </div>
    </section>

    <!-- ========== 第四行：详细数据分析 ========== -->
    <section class="legacy-section">
      <div class="body-area">
        <!-- 左侧：实时弹幕列表 -->
        <section class="panel danmu-panel">
          <DanmuList :list="danmuList" />
        </section>

        <!-- 右侧：情绪 + 主内容 -->
        <div class="right-area">
          <div class="sentiment-area">
            <div class="sentiment-row">
              <div class="panel sentiment-left">
                <RealtimeSentiment :data="realtimeSentiment" />
              </div>
              <div class="panel sentiment-right">
                <SentimentChart :data="sentimentData" :elapsed="elapsedSeconds" />
              </div>
            </div>
          </div>

          <main class="main-content">
            <div class="panel-center">
              <div class="chart-row panel">
                <WordCloud :words="topWords" />
              </div>
              <div class="chart-row panel">
                <TrendChart :data="trendData" />
              </div>
            </div>
            <section class="panel">
              <UserRank :users="topUsers" />
            </section>
          </main>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
console.log('[App.vue v3.0] 组件开始加载...')

import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'

// ===== v1.0 原有组件 =====
import DanmuList from './components/DanmuList.vue'
import WordCloud from './components/WordCloud.vue'
import TrendChart from './components/TrendChart.vue'
import UserRank from './components/UserRank.vue'
import SentimentChart from './components/SentimentChart.vue'
import RealtimeSentiment from './components/RealtimeSentiment.vue'

// ===== v3.0 新增组件 =====
import SatisfactionGauge from './components/SatisfactionGauge.vue'
import HeatCard from './components/HeatCard.vue'
import RiskCard from './components/RiskCard.vue'
import TopicTop5 from './components/TopicTop5.vue'
import AdvicePanel from './components/AdvicePanel.vue'
import WarningCenter from './components/WarningCenter.vue'
import EmotionTrend from './components/EmotionTrend.vue'

console.log('[App.vue v3.0] 子组件导入完成（7个原有 + 7个新增 = 14个）')

// ============ WebSocket 状态 ============
let ws = null
let reconnectTimer = null
const wsConnected = ref(false)

// ============ 数据状态 ============
const MAX_DANMU = 500
const danmuList = ref([])
const wordCountMap = reactive(new Map())
const trendData = ref([])
const userCountMap = reactive(new Map())

let currentTrendBucket = ''
let currentTrendCount = 0
const MAX_TREND_BUCKETS = 12

// ============ 情绪追踪状态（v1.0 保留） ============
const sentimentData = ref([])
let sentimentBucket = ''
let sentimentPos = 0
let sentimentNeu = 0
let sentimentNeg = 0
const MAX_SENTIMENT_BUCKETS = 20

const realtimeSentiment = ref({ positive: 0, neutral: 0, negative: 0 })
const globalSentiment = ref({ positive: 0, neutral: 0, negative: 0 })

// ============ v3.0 新增运营数据状态 ============
const metrics = ref({
  satisfaction: 50.0,
  heat_index: 0.0,
  risk_level: '低'
})
const topics = ref([])                    // 关注主题 TOP5
const warnings = ref([])                  // 预警列表
const advice = ref([])                    // 运营建议（v3.0 字符串列表）
const warningStatus = ref({               // v3.0 统一预警状态
  level: '🟢', level_text: '正常', negative_rate: 0,
  keywords: [], keywords_detail: [], count: 0, change_5min: '0%', timestamp: ''
})
const structuredAdvice = ref({            // v3.0 结构化建议
  topic: '', hotwords: [], advice: []
})
const liveInfo = reactive({               // v3.1 直播间信息
  anchor_name: '',
  live_title: ''
})
const sentimentTimeline = ref({           // 情绪趋势时间线
  timeline: [],
  positive: [],
  neutral: [],
  negative: []
})

// ============ 开播计时 ============
const startTime = ref(0)
const elapsedSeconds = ref(0)
let elapsedTimer = null

function startElapsedTimer() {
  if (elapsedTimer) return
  startTime.value = Date.now()
  elapsedTimer = setInterval(() => {
    elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 1000)
}

// ============ 计算属性 ============
const uniqueUsers = computed(() => userCountMap.size)

const topWords = computed(() => {
  const arr = []
  for (const [name, value] of wordCountMap) {
    arr.push({ name, value })
  }
  arr.sort((a, b) => b.value - a.value)
  return arr.slice(0, 10)
})

// 严格降序：发言次数从多到少，同分按字母序
const topUsers = computed(() => {
  const arr = []
  for (const [name, value] of userCountMap) {
    arr.push({ name, value })
  }
  arr.sort((a, b) => b.value - a.value || a.name.localeCompare(b.name))
  return arr.slice(0, 10)
})

// ============ 趋势桶 ============
function initTrendData() {
  const now = new Date()
  const result = []
  for (let i = MAX_TREND_BUCKETS - 1; i >= 0; i--) {
    const t = new Date(now.getTime() - i * 5000)
    const h = String(t.getHours()).padStart(2, '0')
    const m = String(t.getMinutes()).padStart(2, '0')
    const s = String(t.getSeconds()).padStart(2, '0')
    result.push({ time: h + ':' + m + ':' + s, count: 0 })
  }
  trendData.value = result
  currentTrendBucket = result[result.length - 1].time
  currentTrendCount = 0
}

function getTrendBucket() {
  const now = new Date()
  const sec = Math.floor(now.getSeconds() / 5) * 5
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  const s = String(sec).padStart(2, '0')
  return h + ':' + m + ':' + s
}

// ============ 累计情绪趋势 ============
function initSentimentData() {
  const now = new Date()
  const result = []
  for (let i = MAX_SENTIMENT_BUCKETS - 1; i >= 0; i--) {
    const t = new Date(now.getTime() - i * 5000)
    const h = String(t.getHours()).padStart(2, '0')
    const m = String(t.getMinutes()).padStart(2, '0')
    const s = String(Math.floor(t.getSeconds() / 5) * 5).padStart(2, '0')
    result.push({ time: h + ':' + m + ':' + s, positive: 0, neutral: 0, negative: 0 })
  }
  sentimentData.value = result
  sentimentBucket = result[result.length - 1].time
  sentimentPos = 0
  sentimentNeu = 0
  sentimentNeg = 0
}

function updateSentimentBucket(bucket) {
  if (bucket !== sentimentBucket) {
    const arr = sentimentData.value
    arr.push({ time: bucket, positive: sentimentPos, neutral: sentimentNeu, negative: sentimentNeg })
    while (arr.length > MAX_SENTIMENT_BUCKETS) {
      arr.shift()
    }
    sentimentBucket = bucket
  }
}

// ============ 处理弹幕数据（v1.0 逻辑完全保留） ============
function processDanmu(danmu) {
  startElapsedTimer()

  // 1. 更新弹幕列表
  danmuList.value.push(danmu)
  while (danmuList.value.length > MAX_DANMU) {
    danmuList.value.shift()
  }

  // 2. 更新热词
  const words = danmu.words || []
  for (const w of words) {
    wordCountMap.set(w, (wordCountMap.get(w) || 0) + 1)
  }

  // 3. 更新趋势
  const bucket = getTrendBucket()
  if (bucket !== currentTrendBucket) {
    const arr = trendData.value
    if (arr.length > 0) {
      arr[arr.length - 1].count = currentTrendCount
    }
    arr.push({ time: bucket, count: 1 })
    while (arr.length > MAX_TREND_BUCKETS) {
      arr.shift()
    }
    currentTrendBucket = bucket
    currentTrendCount = 1
  } else {
    currentTrendCount++
    const arr = trendData.value
    if (arr.length > 0) {
      arr[arr.length - 1].count = currentTrendCount
    }
  }

  // 4. 更新用户累计
  userCountMap.set(danmu.name, (userCountMap.get(danmu.name) || 0) + 1)

  // 5. 更新情绪趋势
  const sentBucket = getTrendBucket()
  updateSentimentBucket(sentBucket)
  const sentiment = danmu.sentiment || 'neutral'
  if (sentiment === 'positive') sentimentPos++
  else if (sentiment === 'negative') sentimentNeg++
  else sentimentNeu++
  const sArr = sentimentData.value
  if (sArr.length > 0) {
    const cur = sArr[sArr.length - 1]
    cur.positive = sentimentPos
    cur.neutral = sentimentNeu
    cur.negative = sentimentNeg
  }
}

// ============ 处理 v3.0/v3.0 运营指标数据 ============
function processMetrics(msg) {
  // 更新运营指标
  if (msg.metrics) {
    metrics.value = {
      satisfaction: msg.metrics.satisfaction ?? metrics.value.satisfaction,
      heat_index: msg.metrics.heat_index ?? metrics.value.heat_index,
      risk_level: msg.metrics.risk_level ?? metrics.value.risk_level
    }
  }
  // 更新关注主题
  if (msg.topics) {
    topics.value = msg.topics
  }
  // 更新预警
  if (msg.warnings) {
    if (msg.new_warnings && msg.new_warnings.length > 0) {
      warnings.value = [...msg.warnings]
    } else {
      warnings.value = msg.warnings
    }
  }
  // 更新运营建议
  if (msg.advice) {
    advice.value = msg.advice
  }
  // v3.0 新增：统一预警状态
  if (msg.warning_status) {
    warningStatus.value = {
      level: msg.warning_status.level || '🟢',
      level_text: msg.warning_status.level_text || '正常',
      negative_rate: msg.warning_status.negative_rate ?? 0,
      keywords: msg.warning_status.keywords || [],
      keywords_detail: msg.warning_status.keywords_detail || [],
      count: msg.warning_status.count || 0,
      change_5min: msg.warning_status.change_5min || '0%',
      timestamp: msg.warning_status.timestamp || ''
    }
  }
  // v3.0 新增：结构化建议
  if (msg.structured_advice) {
    structuredAdvice.value = {
      topic: msg.structured_advice.topic || '',
      hotwords: msg.structured_advice.hotwords || [],
      advice: msg.structured_advice.advice || []
    }
  }
  // v3.1 新增：直播间信息
  if (msg.live_info) {
    if (msg.live_info.anchor_name) {
      liveInfo.anchor_name = msg.live_info.anchor_name
    }
    if (msg.live_info.live_title) {
      liveInfo.live_title = msg.live_info.live_title
    }
  }
  // 更新情绪时间线（来自定期推送）
  if (msg.sentiment_timeline) {
    sentimentTimeline.value = msg.sentiment_timeline
  }
}

// ============ WebSocket ============
function connectWebSocket() {
  console.log('[WebSocket] 正在连接 ws://127.0.0.1:8000/ws ...')
  try {
    ws = new WebSocket('ws://127.0.0.1:8000/ws')

    ws.onopen = () => {
      console.log('[WebSocket] 连接成功')
      wsConnected.value = true
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)

        // === v3.0/v3.0: 处理运营指标快照消息（定期推送） ===
        if (msg.type === 'metrics_snapshot') {
          if (msg.metrics) {
            metrics.value = {
              satisfaction: msg.metrics.satisfaction ?? metrics.value.satisfaction,
              heat_index: msg.metrics.heat_index ?? metrics.value.heat_index,
              risk_level: msg.metrics.risk_level ?? metrics.value.risk_level
            }
          }
          if (msg.sentiment_timeline) {
            sentimentTimeline.value = msg.sentiment_timeline
          }
          if (msg.warnings) {
            warnings.value = msg.warnings
          }
          if (msg.realtime_sentiment) {
            realtimeSentiment.value = msg.realtime_sentiment
          }
          // v3.0 新增
          if (msg.warning_status) {
            warningStatus.value = {
              level: msg.warning_status.level || '🟢',
              level_text: msg.warning_status.level_text || '正常',
              negative_rate: msg.warning_status.negative_rate ?? 0,
              keywords: msg.warning_status.keywords || [],
              keywords_detail: msg.warning_status.keywords_detail || [],
              count: msg.warning_status.count || 0,
              change_5min: msg.warning_status.change_5min || '0%',
              timestamp: msg.warning_status.timestamp || ''
            }
          }
          // v3.1 新增：直播间信息
          if (msg.live_info) {
            if (msg.live_info.anchor_name) {
              liveInfo.anchor_name = msg.live_info.anchor_name
            }
            if (msg.live_info.live_title) {
              liveInfo.live_title = msg.live_info.live_title
            }
          }
          return
        }

        // === v1.0: 处理弹幕消息 ===
        if (msg.realtime_sentiment) {
          realtimeSentiment.value = msg.realtime_sentiment
        }
        if (msg.global_sentiment) {
          globalSentiment.value = msg.global_sentiment
        }

        // === v3.0: 处理运营指标 ===
        processMetrics(msg)

        // 原有弹幕处理逻辑（保持 v1.0 行为）
        processDanmu(msg)
      } catch (e) {
        console.error('[WebSocket] 解析失败:', e)
      }
    }

    ws.onclose = () => {
      console.log('[WebSocket] 连接关闭, 3秒后重连')
      wsConnected.value = false
      reconnectTimer = setTimeout(connectWebSocket, 3000)
    }

    ws.onerror = () => {
      console.error('[WebSocket] 连接错误 (后端可能未启动)')
    }
  } catch (e) {
    console.error('[WebSocket] 创建失败:', e)
  }
}

function startHeartbeat() {
  setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send('ping')
    }
  }, 30000)
}

// ============ 生命周期 ============
onMounted(() => {
  console.log('[App.vue v3.0] 组件已挂载')
  initTrendData()
  initSentimentData()
  connectWebSocket()
  startHeartbeat()
})

onUnmounted(() => {
  if (ws) { ws.close(); ws = null }
  if (reconnectTimer) { clearTimeout(reconnectTimer) }
  if (elapsedTimer) { clearInterval(elapsedTimer) }
})

console.log('[App.vue v3.0] 组件初始化完成')
</script>

<!-- 全局样式 -->
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: #0a0e1a;
  color: #e0e6ff;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  min-height: 100vh;
  overflow-x: hidden;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
::-webkit-scrollbar-thumb { background: rgba(100,255,218,0.2); border-radius: 3px; }
</style>

<!-- 组件样式 -->
<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 12px;
  gap: 10px;
  background-image:
    linear-gradient(rgba(100,255,218,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(100,255,218,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* ========== 顶部标题栏 ========== */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: rgba(20,30,60,0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(100,255,218,0.15);
  border-radius: 12px;
  flex-shrink: 0;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.logo-icon { color: #64ffda; font-size: 20px; animation: pulse 2s infinite; }
@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
.title {
  font-size: 18px;
  font-weight: 700;
  color: #64ffda;
  letter-spacing: 2px;
  font-family: 'Consolas', 'Courier New', monospace;
}
.version-tag {
  font-size: 10px; color: #8892b0;
  background: rgba(100,255,218,0.1);
  padding: 2px 6px; border-radius: 4px;
  border: 1px solid rgba(100,255,218,0.2);
}
.header-right { display: flex; align-items: center; gap: 24px; }

.status-badge {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 20px; font-size: 12px;
  background: rgba(255,107,107,0.15); color: #ff6b6b;
}
.status-badge.connected {
  background: rgba(100,255,218,0.15); color: #64ffda;
}
.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: currentColor; animation: pulse 2s infinite;
}

.stat-item { display: flex; flex-direction: column; align-items: center; }
.stat-label { font-size: 11px; color: #8892b0; text-transform: uppercase; letter-spacing: 1px; }
.stat-value {
  font-size: 20px; font-weight: 700; color: #64ffda;
  font-family: 'Consolas', 'Courier New', monospace;
}

/* ========== 通用面板 ========== */
.panel {
  background: rgba(20,30,60,0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(100,255,218,0.15);
  border-radius: 10px;
  padding: 12px;
  overflow: hidden;
}

/* ========== v3.1 直播间信息栏 ========== */
.live-info-bar {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 10px 20px;
  background: rgba(20,30,60,0.5);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(100,255,218,0.12);
  border-radius: 10px;
  flex-shrink: 0;
  overflow: hidden;
}
.live-info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex-shrink: 1;
}
.live-info-title-item {
  flex: 1;
  min-width: 0;
}
.live-info-icon {
  font-size: 16px;
  flex-shrink: 0;
}
.live-info-label {
  font-size: 11px;
  color: #5a6680;
  flex-shrink: 0;
  margin-right: 2px;
}
.live-info-value {
  font-size: 13px;
  font-weight: 600;
  color: #e0e6ff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.live-info-title-text {
  color: #64ffda;
}
.live-info-divider {
  width: 1px;
  height: 20px;
  background: rgba(100,255,218,0.15);
  margin: 0 20px;
  flex-shrink: 0;
}

/* ========== 响应式：小屏时信息栏换行 ========== */
@media (max-width: 768px) {
  .live-info-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
  .live-info-divider {
    display: none;
  }
  .live-info-value {
    font-size: 12px;
  }
}

/* ========== 第一行：运营核心指标 ========== */
.metrics-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  flex-shrink: 0;
}
.metric-panel {
  height: 170px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ========== 第二行：关注主题 + 运营建议 ========== */
.topics-advice-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  flex-shrink: 0;
}
.topics-panel {
  height: 220px;
}
.advice-panel-wrap {
  height: 220px;
}

/* ========== 第三行：情绪趋势 + 预警（并排） ========== */
.trend-warn-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  flex-shrink: 0;
}
.trend-warn-panel {
  height: 200px;
}

/* ========== 第四行：原有功能组件区（可折叠） ========== */
.legacy-section {
  flex-shrink: 0;
}
.body-area {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  height: 950px;
}
.danmu-panel {
  flex: 0 0 300px;
  overflow: hidden;
}

.right-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

/* 情绪分析区 */
.sentiment-area {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.sentiment-row {
  display: flex;
  gap: 10px;
  height: 340px;
}
.sentiment-left {
  flex: 20;
  min-width: 220px;
  overflow: visible;
}
.sentiment-right {
  flex: 80;
  overflow: hidden;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 12px;
  min-height: 0;
}
.panel-center {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chart-row {
  flex: 1;
  min-height: 0;
}
/* WordCloud: 压缩高度 */
.chart-row:first-child {
  flex: 0 0 42%;
}
/* TrendChart: 保持较大面积 */
.chart-row:last-child {
  flex: 1 1 58%;
}
</style>
