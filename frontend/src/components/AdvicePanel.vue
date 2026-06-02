<!--
AdvicePanel.vue — 运营建议面板
卡片形式展示多条运营优化建议，支持滚动
-->
<template>
  <div class="ap-wrap">
    <div class="ap-head">
      <span class="ap-dot"></span>
      <span class="ap-title">运营建议</span>
      <span class="ap-badge">{{ list.length }} 条</span>
    </div>
    <div class="ap-body" ref="scrollBox">
      <div v-if="list.length === 0" class="ap-empty">
        <span>📋</span>
        <span>等待数据分析...</span>
      </div>
      <div
        v-for="(item, idx) in list"
        :key="idx"
        class="ap-item"
      >
        <div class="ap-item-num">{{ idx + 1 }}</div>
        <div class="ap-item-text">{{ item }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  list: { type: Array, default: () => [] }
})
</script>

<style scoped>
.ap-wrap { display: flex; flex-direction: column; height: 100%; }
.ap-head {
  display: flex; align-items: center; gap: 6px;
  padding-bottom: 10px; border-bottom: 1px solid rgba(100,255,218,0.15);
  flex-shrink: 0;
}
.ap-dot { font-size: 10px; color: #ffd43b; }
.ap-title { font-size: 14px; font-weight: 600; color: #64ffda; }
.ap-badge {
  margin-left: auto; font-size: 10px;
  background: rgba(255,212,59,0.15); color: #ffd43b;
  padding: 2px 8px; border-radius: 10px;
}
.ap-body {
  flex: 1; overflow-y: auto; margin-top: 8px;
  display: flex; flex-direction: column; gap: 8px;
}
.ap-empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; color: #8892b0;
  font-size: 13px; gap: 6px;
}
.ap-item {
  display: flex; gap: 10px; align-items: flex-start;
  padding: 10px 12px;
  background: rgba(255,255,255,0.02);
  border-left: 3px solid rgba(255,212,59,0.4);
  border-radius: 0 8px 8px 0;
  transition: all 0.3s;
}
.ap-item:hover {
  background: rgba(255,212,59,0.05);
  border-left-color: #ffd43b;
}
.ap-item-num {
  width: 22px; height: 22px; border-radius: 50%;
  background: rgba(255,212,59,0.15); color: #ffd43b;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.ap-item-text {
  font-size: 12px; color: #e0e6ff; line-height: 1.5; flex: 1;
}
</style>
