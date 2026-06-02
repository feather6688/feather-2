<!--
HeatCard.vue — 热度指数卡片
显示直播间实时热度指数（0~100），带进度条动画
-->
<template>
  <div class="hc-wrap">
    <div class="hc-head">
      <span class="hc-icon">🔥</span>
      <span class="hc-title">热度指数</span>
      <span class="hc-badge live">🔴 LIVE</span>
    </div>
    <div class="hc-body">
      <div class="hc-value" :style="{ color: heatColor }">{{ displayValue }}</div>
      <div class="hc-bar-track">
        <div class="hc-bar-fill" :style="{ width: displayValue + '%', background: heatColor }"></div>
      </div>
      <div class="hc-label">{{ heatLabel }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 }
})

const displayValue = computed(() => Math.round(props.value))

const heatColor = computed(() => {
  const v = props.value
  if (v >= 70) return '#ff6b6b'
  if (v >= 40) return '#ffa94d'
  if (v >= 15) return '#ffd43b'
  return '#00cfff'
})

const heatLabel = computed(() => {
  const v = props.value
  if (v >= 70) return '🔥 火爆'
  if (v >= 40) return '📈 热门'
  if (v >= 15) return '💬 活跃'
  return '💤 平静'
})
</script>

<style scoped>
.hc-wrap {
  display: flex; flex-direction: column; height: 100%;
  justify-content: center; align-items: center;
}
.hc-head {
  display: flex; align-items: center; gap: 6px; margin-bottom: 12px;
}
.hc-icon { font-size: 20px; }
.hc-title { font-size: 14px; font-weight: 600; color: #e0e6ff; }
.hc-badge {
  font-size: 8px; padding: 1px 5px; border-radius: 3px;
  border: 1px solid #ff6b6b; color: #ff6b6b;
  background: rgba(255,107,107,0.1);
}
.hc-body { text-align: center; width: 100%; padding: 0 20px; }
.hc-value {
  font-size: 48px; font-weight: 700;
  font-family: 'Consolas', 'Courier New', monospace;
  transition: color 0.5s;
  line-height: 1.1;
}
.hc-bar-track {
  width: 100%; height: 8px;
  background: rgba(255,255,255,0.08);
  border-radius: 4px; margin-top: 12px; overflow: hidden;
}
.hc-bar-fill {
  height: 100%; border-radius: 4px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1), background 0.5s;
}
.hc-label {
  font-size: 12px; color: #8892b0; margin-top: 8px;
}
</style>
