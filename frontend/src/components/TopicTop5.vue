<!--
TopicTop5.vue — 关注主题 TOP5 横向柱状图
自动适配容器大小
-->
<template>
  <div class="tt-wrap">
    <div class="tt-head">
      <span class="tt-dot"></span>
      <span class="tt-title">关注主题 TOP5</span>
      <span class="tt-sub">业务关键词聚合</span>
      <span class="tt-badge cumu">📊 累计</span>
    </div>
    <div ref="chartDom" class="tt-body"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ topics: { type: Array, default: () => [] } })
const chartDom = ref(null)
let chart = null

const GRAD_COLORS = [
  new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#ff6b6b' }, { offset: 1, color: '#ff8787' }]),
  new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#ffa94d' }, { offset: 1, color: '#ffc078' }]),
  new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#ffd43b' }, { offset: 1, color: '#ffe066' }]),
  new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#00cfff' }, { offset: 1, color: '#66d9ff' }]),
  new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#00ff99' }, { offset: 1, color: '#66ffc2' }]),
]

function buildOption(list) {
  const has = list && list.length > 0
  const reversed = has ? [...list].reverse() : []
  const names = has ? reversed.map(t => t.name) : []
  const values = has ? reversed.map(t => t.count) : []
  return {
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(8,12,30,0.95)',
      borderColor: 'rgba(100,255,218,0.25)',
      textStyle: { color: '#e0e6ff', fontSize: 12 }
    },
    grid: { left: 60, right: 40, top: 10, bottom: 16 },
    xAxis: {
      type: 'value', minInterval: 1,
      splitLine: { lineStyle: { color: 'rgba(100,255,218,0.05)' } },
      axisLabel: { color: '#8892b0', fontSize: 9 }
    },
    yAxis: {
      type: 'category', data: names,
      axisLine: { lineStyle: { color: 'rgba(100,255,218,0.15)' } },
      axisTick: { show: false },
      axisLabel: { color: '#e0e6ff', fontSize: 11, fontWeight: 600 }
    },
    series: [{
      type: 'bar', barWidth: 18,
      data: values.map((v, i) => ({ value: v, itemStyle: { borderRadius: [0, 6, 6, 0], color: GRAD_COLORS[i] || GRAD_COLORS[4] } })),
      label: { show: true, position: 'right', color: '#8892b0', fontSize: 10, formatter: '{c} 次' },
      animationDuration: 600, animationEasing: 'cubicInOut'
    }]
  }
}

function render() {
  const dom = chartDom.value
  if (!dom || dom.clientWidth === 0 || dom.clientHeight === 0) return
  if (chart) { chart.dispose(); chart = null }
  chart = echarts.init(dom)
  chart.setOption(buildOption(props.topics))
}

function onResize() {
  if (chart && !chart.isDisposed()) chart.resize()
}

onMounted(() => {
  nextTick(() => { setTimeout(() => { render(); onResize() }, 150) })
  window.addEventListener('resize', onResize)
})

watch(() => props.topics, () => {
  if (chart && !chart.isDisposed()) {
    chart.setOption(buildOption(props.topics), true)
    chart.resize()
  } else { render() }
}, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (chart && !chart.isDisposed()) { chart.dispose(); chart = null }
})
</script>

<style scoped>
.tt-wrap { display: flex; flex-direction: column; height: 100%; width: 100%; }
.tt-head {
  display: flex; align-items: center; gap: 6px;
  padding-bottom: 8px; border-bottom: 1px solid rgba(100,255,218,0.15);
  flex-shrink: 0;
}
.tt-dot { font-size: 10px; color: #ffa94d; }
.tt-title { font-size: 14px; font-weight: 600; color: #64ffda; }
.tt-sub { font-size: 10px; color: #8892b0; }
.tt-badge {
  font-size: 8px; margin-left: auto; padding: 1px 5px; border-radius: 3px;
}
.tt-badge.cumu {
  border: 1px solid #ffd43b; color: #ffd43b;
  background: rgba(255,212,59,0.1);
}
.tt-body { flex: 1; min-height: 0; width: 100%; }
</style>
