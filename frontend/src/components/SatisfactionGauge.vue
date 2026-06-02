<!--
SatisfactionGauge.vue — 用户满意度仪表盘
使用 ECharts Gauge 展示 0~100 满意度分数，支持动画刷新
-->
<template>
  <div class="sg-wrap">
    <div class="sg-head">
      <span class="sg-dot"></span>
      <span class="sg-title">用户满意度</span>
    </div>
    <div ref="chartDom" class="sg-body"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  value: { type: Number, default: 50 }
})

const chartDom = ref(null)
let chart = null

function buildOption(val) {
  return {
    series: [{
      type: 'gauge',
      startAngle: 200,
      endAngle: -20,
      center: ['50%', '55%'],
      radius: '90%',
      min: 0,
      max: 100,
      splitNumber: 10,
      axisLine: {
        show: true,
        lineStyle: {
          width: 14,
          color: [
            [0.3, '#ff6b6b'],
            [0.6, '#ffa94d'],
            [0.8, '#ffd43b'],
            [1, '#00ff99']
          ]
        }
      },
      pointer: {
        length: '60%',
        width: 5,
        itemStyle: { color: '#e0e6ff' }
      },
      axisTick: {
        distance: -14,
        length: 6,
        lineStyle: { color: '#8892b0', width: 1 }
      },
      splitLine: {
        distance: -16,
        length: 12,
        lineStyle: { color: '#8892b0', width: 2 }
      },
      axisLabel: {
        color: '#8892b0',
        fontSize: 9,
        distance: 20,
        formatter: '{value}'
      },
      detail: {
        valueAnimation: true,
        formatter: (v) => Math.round(v) + '',
        color: '#e0e6ff',
        fontSize: 36,
        fontWeight: 'bold',
        fontFamily: 'Consolas, Courier New, monospace',
        offsetCenter: [0, '55%']
      },
      data: [{ value: val }],
      animationDuration: 600,
      animationEasing: 'cubicInOut'
    }]
  }
}

function initChart() {
  const dom = chartDom.value
  if (!dom || dom.clientWidth === 0) { setTimeout(initChart, 150); return }
  chart = echarts.init(dom)
  chart.setOption(buildOption(props.value))
}

watch(() => props.value, (v) => {
  if (chart) chart.setOption(buildOption(v), true)
})

onMounted(() => {
  nextTick(() => initChart())
  window.addEventListener('resize', () => { if (chart) chart.resize() })
})

onUnmounted(() => {
  window.removeEventListener('resize', () => {})
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.sg-wrap {
  display: flex; flex-direction: column; height: 100%; width: 100%;
}
.sg-head {
  display: flex; align-items: center; gap: 6px;
  padding-bottom: 2px; flex-shrink: 0;
}
.sg-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #64ffda;
  box-shadow: 0 0 8px rgba(100,255,218,0.6);
}
.sg-title { font-size: 12px; font-weight: 600; color: #e0e6ff; }
.sg-body { flex: 1; width: 100%; min-height: 0; }
</style>
