<!--
RiskCard.vue — 风险等级卡片
展示当前直播间风险等级（低/中/高），带颜色指示
-->
<template>
  <div class="rc-wrap" :class="riskClass">
    <div class="rc-head">
      <span class="rc-icon">{{ riskIcon }}</span>
      <span class="rc-title">风险等级</span>
    </div>
    <div class="rc-body">
      <div class="rc-badge" :class="riskClass">
        <span class="rc-level">{{ level }}</span>
        <span class="rc-text">风险</span>
      </div>
      <div class="rc-desc">{{ riskDesc }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  level: { type: String, default: '低' }
})

const riskClass = computed(() => {
  const map = { '高': 'risk-high', '中': 'risk-mid', '低': 'risk-low' }
  return map[props.level] || 'risk-low'
})

const riskIcon = computed(() => {
  const map = { '高': '🚨', '中': '⚠️', '低': '✅' }
  return map[props.level] || '✅'
})

const riskDesc = computed(() => {
  const map = {
    '高': '负面反馈较多，需立即关注',
    '中': '存在一定负面反馈，建议留意',
    '低': '直播间氛围良好，运转正常'
  }
  return map[props.level] || '—'
})
</script>

<style scoped>
.rc-wrap {
  display: flex; flex-direction: column; height: 100%;
  justify-content: center; align-items: center;
  transition: all 0.3s;
}
.rc-head {
  display: flex; align-items: center; gap: 6px; margin-bottom: 16px;
}
.rc-icon { font-size: 20px; }
.rc-title { font-size: 14px; font-weight: 600; color: #e0e6ff; }
.rc-body { text-align: center; }
.rc-badge {
  display: inline-flex; align-items: baseline; gap: 4px;
  padding: 12px 28px; border-radius: 16px;
  transition: all 0.3s;
}
.rc-level {
  font-size: 42px; font-weight: 700;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}
.rc-text { font-size: 16px; opacity: 0.8; }
.rc-desc { font-size: 11px; color: #8892b0; margin-top: 10px; }

/* 高风险 — 红色 */
.risk-high .rc-badge {
  background: rgba(255,107,107,0.15);
  border: 1px solid rgba(255,107,107,0.4);
  color: #ff6b6b;
  box-shadow: 0 0 20px rgba(255,107,107,0.2);
}
/* 中风险 — 黄色 */
.risk-mid .rc-badge {
  background: rgba(255,169,77,0.15);
  border: 1px solid rgba(255,169,77,0.4);
  color: #ffa94d;
  box-shadow: 0 0 20px rgba(255,169,77,0.2);
}
/* 低风险 — 绿色 */
.risk-low .rc-badge {
  background: rgba(0,255,153,0.1);
  border: 1px solid rgba(0,255,153,0.3);
  color: #00ff99;
  box-shadow: 0 0 20px rgba(0,255,153,0.15);
}
</style>
