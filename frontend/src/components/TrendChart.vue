<!--
TrendChart.vue — 弹幕趋势折线图（含每5秒弹幕计数）
-->
<template>
  <div class="tc-container">
    <div class="tc-title">
      <span class="tc-dot">&#9679;</span> 实时弹幕趋势
      <span class="tc-unit">（每5秒采样）</span>
      <span class="tc-badge live">🔴 LIVE</span>
      <!-- 右上角：当前5秒桶弹幕数量 -->
      <div class="tc-counter">
        <span class="tc-counter-label">当前</span>
        <span class="tc-counter-value">{{ currentCount }}</span>
        <span class="tc-counter-label">条/5s</span>
      </div>
    </div>
    <div ref="chartRef" class="tc-chart"></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ data: { type: Array, required: true } })
const chartRef = ref(null)
let chart = null

// 当前5秒桶的弹幕数量（取数据最后一个点的 count）
const currentCount = computed(() => {
  if (!props.data || props.data.length === 0) return 0
  return props.data[props.data.length - 1].count
})

function buildOption(data) {
  const times = data.map(d => d.time)
  const counts = data.map(d => d.count)
  const allZero = counts.every(c => c === 0)
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(20,30,60,0.95)',
      borderColor: 'rgba(100,255,218,0.3)',
      textStyle: { color: '#e0e6ff', fontSize: 12 },
      formatter: (p) => p[0].axisValue + '<br/>弹幕: <b>' + p[0].value + '</b>'
    },
    grid: { left: 40, right: 20, top: 15, bottom: 30 },
    xAxis: {
      type: 'category', data: times, boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(100,255,218,0.2)' } },
      axisTick: { show: false },
      axisLabel: { color: '#8892b0', fontSize: 9, rotate: 30 }
    },
    yAxis: {
      type: 'value', minInterval: 1,
      splitLine: { lineStyle: { color: 'rgba(100,255,218,0.05)' } },
      axisLabel: { color: '#8892b0', fontSize: 9 }
    },
    series: [{
      type: 'line', data: counts, smooth: true,
      symbol: 'circle', symbolSize: 5,
      showSymbol: !allZero,
      lineStyle: { color: '#64ffda', width: 2 },
      itemStyle: { color: '#64ffda', borderColor: '#0a0e1a', borderWidth: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(100,255,218,0.3)' },
          { offset: 1, color: 'rgba(100,255,218,0.01)' }
        ])
      }
    }]
  }
}

function initChart() {
  const dom = chartRef.value
  if (!dom) return
  if (dom.clientWidth === 0 || dom.clientHeight === 0) {
    console.warn('[TrendChart] 容器尺寸为0，延迟初始化')
    setTimeout(initChart, 200)
    return
  }
  chart = echarts.init(dom)
  chart.setOption(buildOption(props.data))
}

function onResize() {
  if (chart && chartRef.value) {
    chart.resize()
  }
}

onMounted(() => {
  nextTick(() => {
    initChart()
  })
  window.addEventListener('resize', onResize)
})

watch(() => props.data, (v) => {
  if (chart) {
    chart.setOption(buildOption(v))
  }
}, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.tc-container { display: flex; flex-direction: column; height: 100%; min-height: 200px; }
.tc-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 14px; font-weight: 600; color: #64ffda;
  padding-bottom: 12px; border-bottom: 1px solid rgba(100,255,218,0.15);
  flex-shrink: 0; margin-bottom: 4px;
}
.tc-dot { font-size: 10px; }
.tc-unit { font-size: 11px; font-weight: 400; color: #8892b0; }
.tc-badge {
  font-size: 9px; margin-left: auto; padding: 1px 5px; border-radius: 3px;
}
.tc-badge.live {
  border: 1px solid #ff6b6b; color: #ff6b6b;
  background: rgba(255,107,107,0.1);
}

/* 右上角：当前5秒计数 */
.tc-counter {
  margin-left: auto;
  display: flex;
  align-items: baseline;
  gap: 4px;
  background: rgba(100,255,218,0.08);
  border: 1px solid rgba(100,255,218,0.2);
  border-radius: 6px;
  padding: 2px 10px;
}
.tc-counter-label {
  font-size: 10px;
  color: #8892b0;
}
.tc-counter-value {
  font-size: 16px;
  font-weight: 700;
  color: #64ffda;
  font-family: 'Consolas', 'Courier New', monospace;
}

.tc-chart { flex: 1; min-height: 150px; width: 100%; }
</style>
