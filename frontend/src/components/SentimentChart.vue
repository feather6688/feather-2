<!--
SentimentChart.vue — 累计情绪分析趋势图
三条折线（正向累计/中性累计/负向累计），持续增长，图例固定显示
-->
<template>
  <div class="sc-wrap">
    <div class="sc-head">
      <span class="sc-dot"></span>
      <span class="sc-title">累计情绪分析</span>
      <span class="sc-badge cumu">📊 累计</span>
      <span class="sc-elapsed">({{ elapsedStr }})</span>
      <div class="sc-stats">
        <div class="sc-stat pos">
          <span class="sc-stat-val">{{ posPercent }}%</span>
          <span class="sc-stat-label">正向</span>
        </div>
        <div class="sc-stat neu">
          <span class="sc-stat-val">{{ neuPercent }}%</span>
          <span class="sc-stat-label">中性</span>
        </div>
        <div class="sc-stat neg">
          <span class="sc-stat-val">{{ negPercent }}%</span>
          <span class="sc-stat-label">负向</span>
        </div>
      </div>
    </div>
    <div ref="chartDom" class="sc-body"></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, required: true },
  elapsed: { type: Number, default: 0 }
})

const chartDom = ref(null)
let chart = null

const elapsedStr = computed(() => {
  const s = props.elapsed || 0
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}时${m}分${sec}秒`
  if (m > 0) return `${m}分${sec}秒`
  return `${sec}秒`
})

const posPercent = computed(() => calcPercent('positive'))
const neuPercent = computed(() => calcPercent('neutral'))
const negPercent = computed(() => calcPercent('negative'))

function calcPercent(key) {
  if (!props.data || props.data.length === 0) return 0
  const last = props.data[props.data.length - 1]
  const total = (last.positive || 0) + (last.neutral || 0) + (last.negative || 0)
  if (total === 0) return 0
  return Math.round((last[key] || 0) / total * 100)
}

function buildOption(raw) {
  const times = (raw && raw.length) ? raw.map(d => d.time) : []
  const pos = (raw && raw.length) ? raw.map(d => d.positive) : []
  const neu = (raw && raw.length) ? raw.map(d => d.neutral) : []
  const neg = (raw && raw.length) ? raw.map(d => d.negative) : []

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(8,12,30,0.95)',
      borderColor: 'rgba(100,255,218,0.25)',
      textStyle: { color: '#e0e6ff', fontSize: 12 },
      axisPointer: { type: 'cross', crossStyle: { color: '#8892b0' } }
    },
    // 图例顶部居中
    legend: {
      top: 10, left: 'center',
      textStyle: { color: '#e0e6ff', fontSize: 11 },
      data: ['正向累计', '中性累计', '负向累计'],
      itemWidth: 14, itemHeight: 8, itemGap: 18,
      selectedMode: false
    },
    // 小边距铺满卡片
    grid: { left: '3%', right: '3%', top: '13%', bottom: '8%', containLabel: true },
    xAxis: {
      type: 'category', data: times, boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(100,255,218,0.2)' } },
      axisTick: { show: false },
      axisLabel: { color: '#8892b0', fontSize: 10, rotate: 0 },
      show: times.length > 0
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: 'rgba(100,255,218,0.05)' } },
      axisLabel: { color: '#8892b0', fontSize: 10 }
    },
    series: [
      {
        name: '正向累计', type: 'line', data: pos,
        smooth: true, symbol: 'none',
        lineStyle: { color: '#00ff99', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0,255,153,0.2)' },
            { offset: 1, color: 'rgba(0,255,153,0.0)' }
          ])
        },
        animationDuration: 400
      },
      {
        name: '中性累计', type: 'line', data: neu,
        smooth: true, symbol: 'none',
        lineStyle: { color: '#00cfff', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0,207,255,0.15)' },
            { offset: 1, color: 'rgba(0,207,255,0.0)' }
          ])
        },
        animationDuration: 400
      },
      {
        name: '负向累计', type: 'line', data: neg,
        smooth: true, symbol: 'none',
        lineStyle: { color: '#ff6b6b', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255,107,107,0.15)' },
            { offset: 1, color: 'rgba(255,107,107,0.0)' }
          ])
        },
        animationDuration: 400
      }
    ]
  }
}

function render() {
  const dom = chartDom.value
  if (!dom || dom.clientWidth === 0 || dom.clientHeight === 0) return
  if (chart) { chart.dispose(); chart = null }
  chart = echarts.init(dom)
  chart.setOption(buildOption(props.data))
}

function onResize() {
  if (chart && !chart.isDisposed()) chart.resize()
}

watch(() => props.data, (v) => {
  if (chart && !chart.isDisposed()) {
    chart.setOption(buildOption(v), true)
  } else { render() }
}, { deep: true })

onMounted(() => {
  nextTick(() => { setTimeout(() => { render(); onResize() }, 150) })
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (chart && !chart.isDisposed()) { chart.dispose(); chart = null }
})
</script>

<style scoped>
.sc-wrap { display: flex; flex-direction: column; height: 100%; width: 100%; }
.sc-head {
  display: flex; align-items: center; gap: 8px;
  padding-bottom: 6px; border-bottom: 1px solid rgba(100,255,218,0.12);
  flex-shrink: 0;
}
.sc-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #64ffda;
  box-shadow: 0 0 8px rgba(100,255,218,0.6);
}
.sc-title { font-size: 14px; font-weight: 700; color: #64ffda; letter-spacing: 1px; }
.sc-badge { font-size: 8px; padding: 1px 5px; border-radius: 3px; margin-left: 6px; }
.sc-badge.cumu { border: 1px solid #ffd43b; color: #ffd43b; background: rgba(255,212,59,0.1); }
.sc-elapsed { font-size: 14px; color: #8ab4c8; font-family: 'Consolas', 'Courier New', monospace; font-weight: 600; }
.sc-stats { margin-left: auto; display: flex; gap: 16px; }
.sc-stat { display: flex; align-items: baseline; gap: 3px; }
.sc-stat-val { font-size: 16px; font-weight: 700; font-family: 'Consolas', 'Courier New', monospace; }
.sc-stat-label { font-size: 10px; color: #8892b0; }
.sc-stat.pos .sc-stat-val { color: #00ff99; }
.sc-stat.neu .sc-stat-val { color: #00cfff; }
.sc-stat.neg .sc-stat-val { color: #ff6b6b; }
.sc-body { flex: 1; min-height: 0; width: 100%; }
</style>
