<!--
WordCloud.vue — 热词圆盘图（南丁格尔玫瑰图）
圆盘居中、占容器60%-70%、标签环绕显示、自动适配大小
-->
<template>
  <div class="wc-wrap">
    <div class="wc-head">
      <span class="wc-dot">&#9679;</span> 累计热词
      <span class="wc-sub">TOP 10</span>
      <span class="wc-badge cumu">📊 累计</span>
    </div>
    <div ref="chartDom" class="wc-body"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ words: { type: Array, required: true } })
const chartDom = ref(null)
let myChart = null

const COLORS = ['#ff6b6b', '#ff8787', '#ffa94d', '#ffc078', '#ffd43b',
  '#ffe066', '#69db7c', '#38d9a9', '#00cfff', '#66d9ff']

function buildOption(list) {
  const pieData = (list && list.length > 0)
    ? list.map((w, i) => ({ name: w.name, value: w.value, itemStyle: { color: COLORS[i] || '#66d9ff' } }))
    : []
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(8,12,30,0.95)',
      borderColor: 'rgba(100,255,218,0.3)',
      textStyle: { color: '#e0e6ff', fontSize: 13 },
      formatter: (p) => `<b>${p.name}</b><br/>出现 ${p.value} 次 (${p.percent}%)`
    },
    series: [{
      type: 'pie',
      center: ['50%', '50%'],
      radius: ['32%', '66%'],
      roseType: 'area',
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 4, borderColor: 'rgba(10,14,26,0.9)', borderWidth: 2 },
      label: {
        show: true, position: 'outside',
        color: '#e0e6ff', fontSize: 12, fontWeight: 600,
        formatter: '{b}'
      },
      labelLine: {
        show: true, length: 24, length2: 18, smooth: false,
        lineStyle: { color: 'rgba(100,255,218,0.35)', width: 1.2 }
      },
      emphasis: { scaleSize: 8, label: { fontSize: 16, fontWeight: 'bold' } },
      data: pieData,
      animationDuration: 500
    }]
  }
}

function render() {
  const dom = chartDom.value
  if (!dom || dom.clientWidth === 0 || dom.clientHeight === 0) return
  if (myChart) { myChart.dispose(); myChart = null }
  myChart = echarts.init(dom)
  myChart.setOption(buildOption(props.words))
}

function onResize() {
  if (myChart && !myChart.isDisposed()) {
    myChart.resize()
  }
}

onMounted(() => {
  nextTick(() => {
    // 等待 DOM 布局完成
    setTimeout(() => { render(); onResize() }, 150)
  })
  window.addEventListener('resize', onResize)
})

watch(() => props.words, () => {
  if (myChart && !myChart.isDisposed()) {
    myChart.setOption(buildOption(props.words), true)
    myChart.resize()
  } else {
    render()
  }
}, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (myChart && !myChart.isDisposed()) { myChart.dispose(); myChart = null }
})
</script>

<style scoped>
.wc-wrap { display: flex; flex-direction: column; height: 100%; width: 100%; }
.wc-head {
  font-size: 14px; font-weight: 600; color: #64ffda;
  padding-bottom: 8px; border-bottom: 1px solid rgba(100,255,218,0.15);
  flex-shrink: 0; display: flex; align-items: center; gap: 6px;
}
.wc-dot { font-size: 10px; }
.wc-sub { font-size: 11px; font-weight: 400; color: #8892b0; }
.wc-badge {
  font-size: 8px; margin-left: auto; padding: 1px 5px; border-radius: 3px;
}
.wc-badge.cumu {
  border: 1px solid #ffd43b; color: #ffd43b;
  background: rgba(255,212,59,0.1);
}
.wc-body { flex: 1; min-height: 0; width: 100%; }
</style>
