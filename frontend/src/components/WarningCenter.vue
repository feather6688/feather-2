<!--
WarningCenter.vue v3.0 — 四等级预警中心
显示：等级图标+颜色、负面率、关键词、数量、5分钟变化
保留 v2.0 业务预警列表和 Tooltip 功能
-->
<template>
  <div class="wc-wrap">
    <div class="wc-head">
      <span class="wc-dot" :class="{ 'wc-active': wstatus.level !== '🟢' }"></span>
      <span class="wc-title">异常预警中心</span>
      <span class="wc-count">{{ warnings.length }} 条</span>
    </div>
    <div class="wc-body">
      <!-- ===== v3.0 四等级预警状态条 ===== -->
      <div class="wc-status-bar" :class="levelClass">
        <div class="wc-status-left">
          <span class="wc-status-icon">{{ wstatus.level }}</span>
          <span class="wc-status-label">{{ wstatus.level_text || '正常' }}</span>
        </div>
        <div class="wc-status-right">
          <span class="wc-status-rate">负面率 {{ ratePct }}%</span>
        </div>
      </div>

      <!-- ===== v3.0 负面关键词统计 ===== -->
      <div class="wc-kw-section" v-if="wstatus.keywords && wstatus.keywords.length > 0">
        <div class="wc-kw-header">
          <span class="wc-kw-label">🔥 负面关键词</span>
          <span class="wc-kw-total">共 {{ wstatus.count }} 次</span>
          <span class="wc-kw-change" :class="changeClass">{{ wstatus.change_5min }}</span>
        </div>
        <div class="wc-kw-tags">
          <span
            v-for="(kw, idx) in wstatus.keywords"
            :key="idx"
            class="wc-kw-tag"
            :style="{ animationDelay: idx * 0.1 + 's' }"
            @mouseenter="showKwTip(kw, $event)"
            @mouseleave="hideKwTip"
          >{{ kw }}</span>
        </div>
      </div>

      <!-- ===== 无数据状态 ===== -->
      <div v-if="warnings.length === 0 && (!wstatus.keywords || wstatus.keywords.length === 0)" class="wc-empty">
        <span class="wc-safe-icon">🛡️</span>
        <span class="wc-safe-text">系统运行正常</span>
        <span class="wc-safe-sub">当前无异常预警信号</span>
      </div>

      <!-- ===== v2.0 保留：业务预警列表 ===== -->
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
      <!-- ===== 业务预警卡片 Tooltip ===== -->
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

      <!-- ===== v3.1 负面关键词弹幕 Tooltip ===== -->
      <transition name="tip-fade">
        <div
          v-if="kwTip"
          class="wc-tooltip wc-kw-tooltip"
          :style="{ left: tipX + 'px', top: tipY + 'px' }"
        >
          <div class="wc-tip-title kw-title">🔥 关键词「{{ kwTip.keyword }}」</div>
          <div class="wc-kw-tip-stats">
            <span>最近5分钟出现 <strong>{{ kwTip.count }}</strong> 次</span>
          </div>
          <div class="wc-kw-tip-samples" v-if="kwTip.samples && kwTip.samples.length > 0">
            <div class="wc-kw-sample-label">📩 弹幕样本：</div>
            <div
              v-for="(s, si) in kwTip.samples"
              :key="si"
              class="wc-kw-sample-item"
            >「{{ s }}」</div>
          </div>
          <div v-else class="wc-kw-tip-no-data">暂无弹幕样本</div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  warnings: { type: Array, default: () => [] },
  // v3.0 新增：统一预警状态
  wstatus: {
    type: Object,
    default: () => ({
      level: '🟢',
      level_text: '正常',
      negative_rate: 0,
      keywords: [],
      count: 0,
      change_5min: '0%',
      timestamp: ''
    })
  }
})

const hasWarning = computed(() => props.warnings.length > 0)

// 负面率百分比
const ratePct = computed(() => Math.round((props.wstatus.negative_rate || 0) * 100))

// 等级对应的 CSS class
const levelClass = computed(() => {
  const lv = props.wstatus.level
  if (lv === '🔴') return 'level-red'
  if (lv === '🟠') return 'level-orange'
  if (lv === '🟡') return 'level-yellow'
  return 'level-green'
})

// 变化百分比样式
const changeClass = computed(() => {
  const ch = props.wstatus.change_5min || '0%'
  if (ch.startsWith('+')) return 'change-up'
  if (ch.startsWith('-')) return 'change-down'
  return 'change-flat'
})

// Tooltip 状态（业务预警卡片）
const activeTip = ref(null)
// Tooltip 状态（负面关键词标签）
const kwTip = ref(null)
const tipX = ref(0)
const tipY = ref(0)

function showTip(idx, event) {
  activeTip.value = props.warnings[idx]
  tipX.value = event.clientX + 14
  tipY.value = event.clientY + 10
}

function hideTip() {
  activeTip.value = null
}

// 根据关键词名从 keywords_detail 中查找详情
function findKwDetail(kwName) {
  const detail = (props.wstatus.keywords_detail || []).find(d => d.keyword === kwName)
  return detail || { keyword: kwName, count: 0, samples: [] }
}

function showKwTip(kwName, event) {
  kwTip.value = findKwDetail(kwName)
  tipX.value = event.clientX + 14
  tipY.value = event.clientY + 10
}

function hideKwTip() {
  kwTip.value = null
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

/* ===== v3.0 预警状态条 ===== */
.wc-status-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; border-radius: 10px;
  transition: all 0.4s ease;
}
.wc-status-bar.level-green  { background: rgba(0,255,153,0.08);  border: 1px solid rgba(0,255,153,0.25); }
.wc-status-bar.level-yellow { background: rgba(255,212,59,0.08);  border: 1px solid rgba(255,212,59,0.35); }
.wc-status-bar.level-orange { background: rgba(255,169,77,0.08);  border: 1px solid rgba(255,169,77,0.40);
                               animation: pulse-orange 2s infinite; }
.wc-status-bar.level-red    { background: rgba(255,107,107,0.1);  border: 1px solid rgba(255,107,107,0.50);
                               animation: pulse-red 1.2s infinite; }

@keyframes pulse-orange { 0%,100%{box-shadow:0 0 4px rgba(255,169,77,0.2)} 50%{box-shadow:0 0 16px rgba(255,169,77,0.45)} }
@keyframes pulse-red    { 0%,100%{box-shadow:0 0 4px rgba(255,107,107,0.2)} 50%{box-shadow:0 0 20px rgba(255,107,107,0.55)} }

.wc-status-left  { display: flex; align-items: center; gap: 8px; }
.wc-status-icon  { font-size: 22px; }
.wc-status-label { font-size: 14px; font-weight: 700; color: #e0e6ff; }
.wc-status-right { text-align: right; }
.wc-status-rate  { font-size: 13px; font-weight: 600; color: #8892b0; font-family: 'Consolas', monospace; }

/* ===== v3.0 负面关键词区域 ===== */
.wc-kw-section {
  padding: 8px 10px;
  background: rgba(255,107,107,0.04);
  border-radius: 8px;
  border-left: 3px solid rgba(255,107,107,0.3);
}
.wc-kw-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
}
.wc-kw-label  { font-size: 12px; font-weight: 600; color: #ff8787; }
.wc-kw-total  { font-size: 11px; color: #8892b0; }
.wc-kw-change { font-size: 12px; font-weight: 700; margin-left: auto; font-family: 'Consolas', monospace; }
.change-up    { color: #ff6b6b; }
.change-down  { color: #00ff99; }
.change-flat  { color: #8892b0; }
.wc-kw-tags {
  display: flex; flex-wrap: wrap; gap: 5px;
}
.wc-kw-tag {
  font-size: 10px; color: #ff8787;
  background: rgba(255,107,107,0.1);
  border: 1px solid rgba(255,107,107,0.2);
  padding: 2px 8px; border-radius: 10px;
  animation: kw-pop 0.3s ease-out both;
}
@keyframes kw-pop { from{opacity:0;transform:scale(0.7)} to{opacity:1;transform:scale(1)} }

/* ===== 空状态 ===== */
.wc-empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; gap: 6px;
}
.wc-safe-icon { font-size: 32px; }
.wc-safe-text { font-size: 15px; font-weight: 700; color: #00ff99; }
.wc-safe-sub { font-size: 11px; color: #5a6680; }

/* ===== v2.0 保留：预警列表项 ===== */
.wc-warn {
  padding: 8px 10px; border-radius: 8px;
  border-left: 4px solid #ff6b6b;
  background: rgba(255,107,107,0.05);
  transition: background 0.2s;
  cursor: pointer;
}
.wc-warn:hover { background: rgba(255,107,107,0.1); }
.wc-warn-row { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; }
.wc-warn-type { font-size: 11px; font-weight: 600; color: #e0e6ff; }
.wc-warn-time { font-size: 10px; color: #8892b0; font-family: 'Consolas', 'Courier New', monospace; }
.wc-warn-freq { margin-left: auto; font-size: 9px; background: rgba(255,107,107,0.2); color: #ff6b6b; padding: 1px 6px; border-radius: 8px; }
.wc-warn-msg  { font-size: 11px; color: #c0c8e0; line-height: 1.4; }
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
.wc-tip-label { font-size: 10px; color: #5a6680; text-align: right; padding-top: 1px; }
.wc-tip-value { font-size: 11px; color: #e0e6ff; word-break: break-all; }
.wc-tip-value.danmu-text { color: #ffd43b; font-style: italic; }
.wc-tip-value.danmu-text .no-data { color: #5a6680; font-style: normal; }
.wc-tip-value.keyword { color: #ff8787; font-weight: 600; }
.wc-tip-value.risk { color: #ff6b6b; font-weight: 700; }

.tip-fade-enter-active { transition: opacity 0.12s; }
.tip-fade-leave-active { transition: opacity 0.08s; }
.tip-fade-enter-from, .tip-fade-leave-to { opacity: 0; }

/* ===== v3.1 关键词 Tooltip 样式 ===== */
.wc-kw-tooltip {
  max-width: 340px;
}
.wc-tip-title.kw-title {
  color: #ffa94d;
}
.wc-kw-tip-stats {
  font-size: 12px; color: #8892b0;
  margin-bottom: 10px; padding-bottom: 8px;
  border-bottom: 1px solid rgba(100,160,255,0.15);
}
.wc-kw-tip-stats strong {
  color: #ff8787; font-family: 'Consolas', monospace;
}
.wc-kw-tip-samples {
  display: flex; flex-direction: column; gap: 6px;
}
.wc-kw-sample-label {
  font-size: 11px; color: #5a6680;
}
.wc-kw-sample-item {
  font-size: 12px; color: #ffd43b; font-style: italic;
  padding: 4px 8px;
  background: rgba(255,212,59,0.05);
  border-left: 2px solid rgba(255,212,59,0.25);
  border-radius: 0 4px 4px 0;
  word-break: break-all;
}
.wc-kw-tip-no-data {
  font-size: 12px; color: #5a6680; font-style: italic;
}
</style>
