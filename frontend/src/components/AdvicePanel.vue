<!--
AdvicePanel.vue v3.0 — 运营建议面板
支持两种模式：
  - 字符串列表（v2.0 兼容，list prop）
  - 结构化 JSON（v3.0 新增，adviceJson prop）
结构化模式显示：话题标签、热词标签、建议列表
-->
<template>
  <div class="ap-wrap">
    <div class="ap-head">
      <span class="ap-dot"></span>
      <span class="ap-title">运营建议</span>
      <span class="ap-badge">{{ totalCount }} 条</span>
    </div>
    <div class="ap-body" ref="scrollBox">
      <!-- ===== 空状态 ===== -->
      <div v-if="!hasData" class="ap-empty">
        <span>📋</span>
        <span>等待数据分析...</span>
      </div>

      <!-- ===== v3.0 结构化建议（优先显示） ===== -->
      <div v-if="adviceJson && adviceJson.topic" class="ap-structured">
        <!-- 话题标题 -->
        <div class="ap-topic-header">
          <span class="ap-topic-icon">💡</span>
          <span class="ap-topic-title">{{ adviceJson.topic }}</span>
        </div>

        <!-- 热词标签 -->
        <div class="ap-hotwords" v-if="adviceJson.hotwords && adviceJson.hotwords.length > 0">
          <span class="ap-hw-label">热词：</span>
          <span
            v-for="(hw, idx) in adviceJson.hotwords"
            :key="idx"
            class="ap-hw-tag"
            :class="'color-' + (idx % 5)"
          >{{ hw }}</span>
        </div>

        <!-- 建议列表 -->
        <div class="ap-advice-list" v-if="adviceJson.advice && adviceJson.advice.length > 0">
          <div
            v-for="(item, idx) in adviceJson.advice"
            :key="'sa-' + idx"
            class="ap-item sa-item"
          >
            <div class="ap-item-num">{{ idx + 1 }}</div>
            <div class="ap-item-text">{{ item }}</div>
          </div>
        </div>
      </div>

      <!-- ===== 分隔线 ===== -->
      <div v-if="adviceJson && adviceJson.topic && list.length > 0" class="ap-divider">
        <span>更多建议</span>
      </div>

      <!-- ===== v2.0 保留：字符串列表建议 ===== -->
      <div
        v-for="(item, idx) in list"
        :key="'l-' + idx"
        class="ap-item"
      >
        <div class="ap-item-num">{{ idx + 1 }}</div>
        <div class="ap-item-text">{{ item }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // v2.0 兼容：字符串列表
  list: { type: Array, default: () => [] },
  // v3.0 新增：结构化建议 JSON
  adviceJson: {
    type: Object,
    default: () => ({ topic: '', hotwords: [], advice: [] })
  }
})

const hasData = computed(() => {
  const hasStructured = !!(props.adviceJson && props.adviceJson.topic)
  const hasList = props.list.length > 0
  return hasStructured || hasList
})

const totalCount = computed(() => {
  let count = 0
  if (props.adviceJson && props.adviceJson.advice) {
    count += props.adviceJson.advice.length
  }
  count += props.list.length
  return count
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

/* ===== v3.0 结构化区域 ===== */
.ap-structured {
  display: flex; flex-direction: column; gap: 8px;
}

/* 话题标题 */
.ap-topic-header {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px;
  background: rgba(100,255,218,0.05);
  border-radius: 8px;
  border: 1px solid rgba(100,255,218,0.12);
}
.ap-topic-icon  { font-size: 16px; }
.ap-topic-title { font-size: 13px; font-weight: 700; color: #64ffda; }

/* 热词标签 */
.ap-hotwords {
  display: flex; align-items: center; flex-wrap: wrap; gap: 5px;
  padding: 4px 0;
}
.ap-hw-label { font-size: 11px; color: #8892b0; flex-shrink: 0; }
.ap-hw-tag {
  font-size: 10px; padding: 2px 8px; border-radius: 10px;
  font-weight: 600;
}
.ap-hw-tag.color-0 { color: #ff6b6b; background: rgba(255,107,107,0.1); border:1px solid rgba(255,107,107,0.2); }
.ap-hw-tag.color-1 { color: #ffa94d; background: rgba(255,169,77,0.1); border:1px solid rgba(255,169,77,0.2); }
.ap-hw-tag.color-2 { color: #ffd43b; background: rgba(255,212,59,0.1); border:1px solid rgba(255,212,59,0.2); }
.ap-hw-tag.color-3 { color: #00cfff; background: rgba(0,207,255,0.1); border:1px solid rgba(0,207,255,0.2); }
.ap-hw-tag.color-4 { color: #00ff99; background: rgba(0,255,153,0.1); border:1px solid rgba(0,255,153,0.2); }

/* ===== 建议列表项 ===== */
.ap-advice-list {
  display: flex; flex-direction: column; gap: 6px;
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
.sa-item {
  border-left-color: rgba(100,255,218,0.4);
}
.sa-item:hover {
  border-left-color: #64ffda;
}
.ap-item-num {
  width: 22px; height: 22px; border-radius: 50%;
  background: rgba(255,212,59,0.15); color: #ffd43b;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.sa-item .ap-item-num {
  background: rgba(100,255,218,0.15); color: #64ffda;
}
.ap-item-text {
  font-size: 12px; color: #e0e6ff; line-height: 1.5; flex: 1;
}

/* ===== 分隔线 ===== */
.ap-divider {
  display: flex; align-items: center; gap: 10px;
  padding: 4px 0;
}
.ap-divider::before, .ap-divider::after {
  content: ''; flex: 1; height: 1px;
  background: rgba(100,255,218,0.1);
}
.ap-divider span {
  font-size: 10px; color: #5a6680; flex-shrink: 0;
}
</style>
