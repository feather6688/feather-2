<!--
EmotionTrend.vue — 情绪趋势图（30分钟窗口）
三线折线图，自动适配容器大小
-->
<template>
  <div class="et-wrap">
    <div class="et-head">
      <span class="et-dot"></span>
      <span class="et-title">实时情绪趋势</span>
      <span class="et-sub">近30分钟 · 30秒采样</span>
      <span class="et-badge live">🔴 LIVE</span>
    </div>
    <div ref="chartDom" class="et-body"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  timeline: { type: Object, default: () => ({ timeline: [], positive: [], neutral: [], negative: [] }) }
})
const chartDom = ref(null)
let chart = null

function buildOption(data) {
  const t = data.timeline || []
  const pos = data.positive || []
  const neu = data.neutral || []
  const neg = data.negative || []
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(8,12,30,0.95)',
      borderColor: 'rgba(100,255,218,0.25)',
      textStyle: { color: '#e0e6ff', fontSize: 12 }
    },
    legend: {
      bottom: 0,
      textStyle: { color: '#8892b0', fontSize: 10 },
      data: ['正向', '中性', '负向'],
      itemWidth: 12, itemHeight: 6, itemGap: 16
    },
    grid: { left: 44, right: 20, top: 16, bottom: 34 },
    xAxis: {
      type: 'category', data: t, boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(100,255,218,0.15)' } },
      axisTick: { show: false },
      axisLabel: { color: '#8892b0', fontSize: 9, rotate: 20 }
    },
    yAxis: {
      type: 'value', minInterval: 1,
      splitLine: { lineStyle: { color: 'rgba(100,255,218,0.05)' } },
      axisLabel: { color: '#8892b0', fontSize: 9 }
    },
    series: [
      {
        name: '正向', type: 'line', data: pos, smooth: true, symbol: 'none',
        lineStyle: { color: '#00ff99', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0,255,153,0.2)' },
            { offset: 1, color: 'rgba(0,255,153,0.0)' }
          ])
        },
        animationDuration: 500, animationEasing: 'cubicInOut'
      },
      {
        name: '中性', type: 'line', data: neu, smooth: true, symbol: 'none',
        lineStyle: { color: '#00cfff', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0,207,255,0.15)' },
            { offset: 1, color: 'rgba(0,207,255,0.0)' }
          ])
        },
        animationDuration: 500, animationEasing: 'cubicInOut'
      },
      {
        name: '负向', type: 'line', data: neg, smooth: true, symbol: 'none',
        lineStyle: { color: '#ff6b6b', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255,107,107,0.2)' },
            { offset: 1, color: 'rgba(255,107,107,0.0)' }
          ])
        },
        animationDuration: 500, animationEasing: 'cubicInOut'
      }
    ]
  }
}

function render() {
  const dom = chartDom.value
  if (!dom || dom.clientWidth === 0 || dom.clientHeight === 0) return
  if (chart) { chart.dispose(); chart = null }
  chart = echarts.init(dom)
  chart.setOption(buildOption(props.timeline))
}

function onResize() {
  if (chart && !chart.isDisposed()) chart.resize()
}

onMounted(() => {
  nextTick(() => { setTimeout(() => { render(); onResize() }, 150) })
  window.addEventListener('resize', onResize)
})

watch(() => props.timeline, () => {
  if (chart && !chart.isDisposed()) {
    chart.setOption(buildOption(props.timeline), true)
    chart.resize()
  } else { render() }
}, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (chart && !chart.isDisposed()) { chart.dispose(); chart = null }
})
</script>

<style scoped>
.et-wrap { display: flex; flex-direction: column; height: 100%; width: 100%; }
.et-head {
  display: flex; align-items: center; gap: 6px;
  padding-bottom: 8px; border-bottom: 1px solid rgba(100,255,218,0.12);
  flex-shrink: 0;
}
.et-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #00cfff;
  box-shadow: 0 0 6px rgba(0,207,255,0.5);
}
.et-title { font-size: 14px; font-weight: 600; color: #64ffda; }
.et-sub { font-size: 10px; color: #8892b0; }
.et-badge {
  font-size: 8px; margin-left: auto; padding: 1px 5px; border-radius: 3px;
}
.et-badge.live {
  border: 1px solid #ff6b6b; color: #ff6b6b;
  background: rgba(255,107,107,0.1);
}
.et-body { flex: 1; min-height: 0; width: 100%; }
</style>
