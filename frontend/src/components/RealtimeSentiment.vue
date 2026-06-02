<!--
RealtimeSentiment.vue — 实时情绪环形图（最近100条弹幕）
左侧标签 + 中间圆盘 + 右侧标签，三列布局，标签永不遮挡圆盘
-->
<template>
  <div class="rs-wrap">
    <div class="rs-head">
      <span class="rs-dot"></span>
      <span class="rs-title">实时情绪分析</span>
      <span class="rs-badge live">🔴 LIVE</span>
    </div>
    <div class="rs-layout">
      <!-- 左侧标签 -->
      <div class="rs-label rs-label-left">
        <div class="rs-item pos">
          <span class="rs-dot-sm dot-pos"></span>
          <span class="rs-name">正向</span>
          <span class="rs-pct">{{ posPct }}%</span>
        </div>
      </div>

      <!-- 中间圆盘 -->
      <div class="rs-chart-wrap">
        <div ref="chartDom" class="rs-chart"></div>
      </div>

      <!-- 右侧标签 -->
      <div class="rs-label rs-label-right">
        <div class="rs-item neu">
          <span class="rs-dot-sm dot-neu"></span>
          <span class="rs-name">中性</span>
          <span class="rs-pct">{{ neuPct }}%</span>
        </div>
        <div class="rs-item neg">
          <span class="rs-dot-sm dot-neg"></span>
          <span class="rs-name">负向</span>
          <span class="rs-pct">{{ negPct }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ data: { type: Object, required: true } })
const chartDom = ref(null)
let chart = null

// 百分比
const total = computed(() => props.data.positive + props.data.neutral + props.data.negative || 1)
const posPct = computed(() => Math.round(props.data.positive / total.value * 100))
const neuPct = computed(() => Math.round(props.data.neutral / total.value * 100))
const negPct = computed(() => Math.round(props.data.negative / total.value * 100))

function buildOption(d) {
  return {
    series: [{
      type: 'pie',
      radius: ['55%', '80%'],
      center: ['50%', '50%'],
      // 关闭 ECharts 自带标签，由 HTML 自定义标签替代
      label: { show: false },
      labelLine: { show: false },
      emphasis: { scaleSize: 4 },
      data: [
        {
          name: '正向', value: d.positive,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
              { offset: 0, color: '#00ff99' }, { offset: 1, color: '#00cc77' }
            ]),
            shadowBlur: 12,
            shadowColor: 'rgba(0,255,153,0.4)'
          }
        },
        {
          name: '中性', value: d.neutral,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
              { offset: 0, color: '#00cfff' }, { offset: 1, color: '#0099cc' }
            ]),
            shadowBlur: 12,
            shadowColor: 'rgba(0,207,255,0.4)'
          }
        },
        {
          name: '负向', value: d.negative,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
              { offset: 0, color: '#ff6b6b' }, { offset: 1, color: '#cc4444' }
            ]),
            shadowBlur: 12,
            shadowColor: 'rgba(255,107,107,0.4)'
          }
        }
      ],
      animationType: 'scale',
      animationEasing: 'elasticOut',
      animationDuration: 600
    }]
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
.rs-wrap {
  display: flex; flex-direction: column; height: 100%;
  padding: 10px;
}
.rs-head {
  display: flex; align-items: center; gap: 6px;
  padding-bottom: 4px; flex-shrink: 0;
}
.rs-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #ff6b6b;
  box-shadow: 0 0 8px rgba(255,107,107,0.7);
  animation: rs-blink 1.2s infinite;
}
@keyframes rs-blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.rs-title { font-size: 12px; font-weight: 700; color: #e0e6ff; }
.rs-badge { font-size: 8px; margin-left: auto; padding: 1px 5px; border-radius: 3px; }
.rs-badge.live { border: 1px solid #ff6b6b; color: #ff6b6b; background: rgba(255,107,107,0.1); animation: rs-blink 1.2s infinite; }

/* ==== 三列布局 ==== */
.rs-layout {
  flex: 1; min-height: 0;
  display: flex; align-items: center; justify-content: center;
  gap: 0;
  padding: 8px 0;
}
/* 左侧标签 */
.rs-label {
  display: flex; flex-direction: column; gap: 10px;
  flex-shrink: 0;
}
.rs-label-left  { align-items: flex-end; padding-right: 6px; }
.rs-label-right { align-items: flex-start; padding-left: 6px; }
/* 每条标签行 */
.rs-item {
  display: flex; align-items: center; gap: 4px;
  white-space: nowrap;
}
.rs-dot-sm {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.dot-pos { background: #00ff99; box-shadow: 0 0 6px rgba(0,255,153,0.5); }
.dot-neu { background: #00cfff; box-shadow: 0 0 6px rgba(0,207,255,0.5); }
.dot-neg { background: #ff6b6b; box-shadow: 0 0 6px rgba(255,107,107,0.5); }
.rs-name { font-size: 11px; color: #8892b0; }
.rs-pct  { font-size: 13px; font-weight: 700; color: #e0e6ff; font-family: 'Consolas','Courier New',monospace; }

/* 中间圆盘：固定尺寸 200×200，最大 240×240 */
.rs-chart-wrap {
  width: 200px; height: 200px; max-width: 240px; max-height: 240px;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.rs-chart { width: 100%; height: 100%; }
</style>
