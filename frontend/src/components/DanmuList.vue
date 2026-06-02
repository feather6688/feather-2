<!--
DanmuList.vue — 实时滚动弹幕列表
-->
<template>
  <div class="dl-container">
    <div class="dl-title">
      <span class="dl-dot">&#9679;</span>
      实时弹幕列表
      <span class="dl-badge live">🔴 LIVE</span>
      <span class="dl-count">({{ showList.length }})</span>
    </div>
    <div class="dl-scroll" ref="scrollBox" @scroll="onScroll">
      <div v-if="showList.length === 0" class="dl-empty">
        <div style="font-size:32px;margin-bottom:8px;">⏳</div>
        <div>等待弹幕中...</div>
        <div style="font-size:11px;opacity:0.5;margin-top:4px;">请打开抖音直播间</div>
      </div>
      <div v-for="(item, index) in showList" :key="index" class="dl-row">
        <div class="dl-avatar">{{ item.name.charAt(0) }}</div>
        <div class="dl-body">
          <div class="dl-head">
            <span class="dl-name">{{ item.name }}</span>
            <span class="dl-time">{{ item.time }}</span>
          </div>
          <div class="dl-text">{{ item.content }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({ list: { type: Array, required: true } })

const scrollBox = ref(null)
const MAX = 100
const autoScroll = ref(true)  // 智能滚动开关

const showList = computed(() => {
  if (props.list.length <= MAX) return props.list
  return props.list.slice(props.list.length - MAX)
})

// 判断是否在底部附近（阈值 50px）
function isNearBottom() {
  const el = scrollBox.value
  if (!el) return false
  return el.scrollHeight - el.scrollTop - el.clientHeight < 50
}

// 用户手动滚动时判断是否退出/恢复自动滚动
function onScroll() {
  autoScroll.value = isNearBottom()
}

// 新弹幕到来时，仅在底部附近才自动滚动
watch(() => props.list.length, async () => {
  await nextTick()
  if (autoScroll.value && scrollBox.value) {
    scrollBox.value.scrollTop = scrollBox.value.scrollHeight
  }
})
</script>

<style scoped>
.dl-container { display: flex; flex-direction: column; height: 100%; }
.dl-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 14px; font-weight: 600; color: #64ffda;
  padding-bottom: 12px; border-bottom: 1px solid rgba(100,255,218,0.15);
  flex-shrink: 0;
}
.dl-dot { font-size: 10px; }
.dl-badge {
  font-size: 9px; margin-left: 6px;
  padding: 1px 5px; border-radius: 3px;
}
.dl-badge.live {
  border: 1px solid #ff6b6b; color: #ff6b6b;
  background: rgba(255,107,107,0.1);
}
.dl-count { font-size: 12px; color: #8892b0; margin-left: auto; }

.dl-scroll {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  margin-top: 8px; padding-right: 4px;
}

.dl-empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 200px; color: #8892b0;
}

.dl-row {
  display: flex; gap: 10px; padding: 8px 10px;
  background: rgba(255,255,255,0.02); border-radius: 8px;
  border-left: 2px solid rgba(100,255,218,0.15); margin-bottom: 4px;
}
.dl-row:hover { background: rgba(100,255,218,0.05); }
.dl-avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; color: #fff; flex-shrink: 0;
}
.dl-body { flex: 1; min-width: 0; }
.dl-head { display: flex; justify-content: space-between; margin-bottom: 2px; }
.dl-name { font-size: 11px; font-weight: 600; color: #64ffda; }
.dl-time { font-size: 10px; color: #8892b0; }
.dl-text { font-size: 13px; color: #e0e6ff; word-break: break-all; line-height: 1.4; }
</style>
