<!--
WarningCenter.vue — 异常预警中心
hover 预警卡片 → 弹出详情 Tooltip（含原始弹幕），移出消失
Teleport 到 body 防止被滚动容器裁切
-->
<template>
  <div class="wc-wrap">
    <div class="wc-head">
      <span class="wc-dot" :class="{ 'wc-active': hasWarning }"></span>
      <span class="wc-title">异常预警中心</span>
      <span class="wc-count">{{ warnings.length }} 条</span>
    </div>
    <div class="wc-body">
      <div v-if="warnings.length === 0" class="wc-empty">
        <span class="wc-safe-icon">🛡️</span>
        <span class="wc-safe-text">系统运行正常</span>
        <span class="wc-safe-sub">过去10分钟无异常预警</span>
      </div>
      <div
        v-for="(w, idx) in warnings"
        :key="idx"
        class="wc-warn"
        @mouseenter="showTip(idx, $event)"
        @mouseleave="hideTip"
      >
        <div class="wc-warn-row">
          <span class="wc-warn-type">{{ typeIcon(w.type) }} {{ w.type_name || w.type }}</span>
          <span class="wc-warn-time">{{ w.time || w.trigger_time || '' }}</span>
          <span class="wc-warn-freq">{{ w.frequency || '' }}次</span>
        </div>
        <div class="wc-warn-msg">{{ w.message }}</div>
      </div>
    </div>

    <!-- Teleport 到 body，永不裁切 -->
    <Teleport to="body">
      <transition name="tip-fade">
        <div
          v-if="activeTip"
          class="wc-tooltip"
          :style="{ left: tipX + 'px', top: tipY + 'px' }"
        >
          <div class="wc-tip-title">{{ activeTip.type_name || activeTip.type }}预警</div>
          <div class="wc-tip-grid">
            <span class="wc-tip-label">用户</span>
            <span class="wc-tip-value">{{ activeTip.trigger_user || '—' }}</span>

            <span class="wc-tip-label">时间</span>
            <span class="wc-tip-value">{{ activeTip.trigger_time || activeTip.time || '—' }}</span>

            <span class="wc-tip-label">弹幕</span>
            <span class="wc-tip-value danmu-text">
              <template v-if="activeTip.trigger_danmu">「{{ activeTip.trigger_danmu }}」</template>
              <span v-else class="no-data">暂无原始弹幕数据</span>
            </span>

            <span class="wc-tip-label">命中词</span>
            <span class="wc-tip-value keyword">{{ activeTip.trigger_keyword || '—' }}</span>

            <span class="wc-tip-label">风险等级</span>
            <span class="wc-tip-value risk">{{ riskLabel(activeTip.level) }}</span>

            <span class="wc-tip-label">触发规则</span>
            <span class="wc-tip-value">{{ activeTip.trigger_rule || activeTip.message }}</span>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  warnings: { type: Array, default: () => [] }
})

const hasWarning = computed(() => props.warnings.length > 0)

// Tooltip 状态
const activeTip = ref(null)
const tipX = ref(0)
const tipY = ref(0)

function showTip(idx, event) {
  activeTip.value = props.warnings[idx]
  // 定位在鼠标右下
  tipX.value = event.clientX + 14
  tipY.value = event.clientY + 10
}

function hideTip() {
  activeTip.value = null
}

function typeIcon(type) {
  const map = { price: '💰', logistics: '📦', aftersale: '🔧', quality: '⚠️' }
  return map[type] || '📢'
}

function riskLabel(level) {
  const map = { high: '高', medium: '中', low: '低' }
  return map[level] || level || '高'
}
</script>

<style scoped>
.wc-wrap { display: flex; flex-direction: column; height: 100%; }
.wc-head {
  display: flex; align-items: center; gap: 6px;
  padding-bottom: 10px; border-bottom: 1px solid rgba(100,255,218,0.15);
  flex-shrink: 0;
}
.wc-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #00ff99; transition: all 0.3s;
}
.wc-dot.wc-active {
  background: #ff6b6b;
  box-shadow: 0 0 8px rgba(255,107,107,0.7);
  animation: wc-blink 1s infinite;
}
@keyframes wc-blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.wc-title { font-size: 14px; font-weight: 600; color: #64ffda; }
.wc-count { margin-left: auto; font-size: 11px; color: #8892b0; }

.wc-body { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
.wc-empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; gap: 6px;
}
.wc-safe-icon { font-size: 32px; }
.wc-safe-text { font-size: 15px; font-weight: 700; color: #00ff99; }
.wc-safe-sub { font-size: 11px; color: #5a6680; }

.wc-warn {
  padding: 8px 10px; border-radius: 8px;
  border-left: 4px solid #ff6b6b;
  background: rgba(255,107,107,0.05);
  transition: background 0.2s;
  cursor: pointer;
}
.wc-warn:hover { background: rgba(255,107,107,0.1); }
.wc-warn-row {
  display: flex; align-items: center; gap: 8px; margin-bottom: 2px;
}
.wc-warn-type { font-size: 11px; font-weight: 600; color: #e0e6ff; }
.wc-warn-time {
  font-size: 10px; color: #8892b0;
  font-family: 'Consolas', 'Courier New', monospace;
}
.wc-warn-freq {
  margin-left: auto; font-size: 9px;
  background: rgba(255,107,107,0.2); color: #ff6b6b;
  padding: 1px 6px; border-radius: 8px;
}
.wc-warn-msg { font-size: 11px; color: #c0c8e0; line-height: 1.4; }
</style>

<!-- ⚠️ 全局样式（非 scoped）：Teleport 到 body 的 Tooltip -->
<style>
.wc-tooltip {
  position: fixed;
  z-index: 99999;
  width: 300px;
  background: rgba(10,15,35,0.98);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(100,160,255,0.5);
  border-radius: 10px;
  padding: 14px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6), 0 0 24px rgba(100,160,255,0.15);
  pointer-events: none;
}
.wc-tip-title {
  font-size: 13px; font-weight: 700; color: #ff6b6b;
  margin-bottom: 10px; padding-bottom: 8px;
  border-bottom: 1px solid rgba(100,160,255,0.25);
}
.wc-tip-grid {
  display: grid;
  grid-template-columns: 55px 1fr;
  gap: 6px 10px;
}
.wc-tip-label {
  font-size: 10px; color: #5a6680; text-align: right; padding-top: 1px;
}
.wc-tip-value {
  font-size: 11px; color: #e0e6ff; word-break: break-all;
}
.wc-tip-value.danmu-text { color: #ffd43b; font-style: italic; }
.wc-tip-value.danmu-text .no-data { color: #5a6680; font-style: normal; }
.wc-tip-value.keyword { color: #ff8787; font-weight: 600; }
.wc-tip-value.risk { color: #ff6b6b; font-weight: 700; }

/* 淡入淡出 */
.tip-fade-enter-active { transition: opacity 0.12s; }
.tip-fade-leave-active { transition: opacity 0.08s; }
.tip-fade-enter-from, .tip-fade-leave-to { opacity: 0; }
</style>
