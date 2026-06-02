<!--
UserRank.vue — 用户活跃排行榜 Top 10
Grid 三列固定布局：奖牌(50px) | 用户名(1fr) | 发言数(60px)
奖牌位置永远不变，超长用户名省略号，hover 显示全名
-->
<template>
  <div class="ur-wrap">
    <div class="ur-head">
      <span class="ur-dot">&#9679;</span> 用户活跃排行
      <span class="ur-sub">Top 10</span>
      <span class="ur-badge cumu">📊 累计</span>
    </div>

    <!-- 表头 -->
    <div class="ur-table-header">
      <span class="ur-col-medal">排名</span>
      <span class="ur-col-name">用户</span>
      <span class="ur-col-count">发言</span>
    </div>

    <!-- 排行列表 -->
    <div class="ur-list">
      <div
        v-for="(user, idx) in rankedUsers"
        :key="user.name"
        class="ur-row"
        :class="{ 'ur-top3': idx < 3 }"
      >
        <!-- 第一列：奖牌固定 50px，水平居中 -->
        <div class="ur-col-medal">
          <span v-if="idx === 0" class="ur-medal medal-gold">🥇</span>
          <span v-else-if="idx === 1" class="ur-medal medal-silver">🥈</span>
          <span v-else-if="idx === 2" class="ur-medal medal-bronze">🥉</span>
          <span v-else class="ur-rank-num">{{ idx + 1 }}</span>
        </div>

        <!-- 第二列：用户名，左对齐，超长省略号 -->
        <div class="ur-col-name" :title="user.name">
          {{ user.name }}
        </div>

        <!-- 第三列：发言次数，右对齐，固定 60px -->
        <div class="ur-col-count">
          {{ user.value }}
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="rankedUsers.length === 0" class="ur-empty">
        等待数据...
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ users: { type: Array, required: true } })

// 严格降序排列：发言最多排第一，同分按名字字母序
const rankedUsers = computed(() => {
  const arr = [...props.users]
  arr.sort((a, b) => {
    // 先按发言次数降序
    const diff = b.value - a.value
    if (diff !== 0) return diff
    // 同分按名字升序
    return a.name.localeCompare(b.name)
  })
  return arr.slice(0, 10)
})
</script>

<style scoped>
.ur-wrap {
  display: flex; flex-direction: column; height: 100%; width: 100%;
}

/* ---- 标题 ---- */
.ur-head {
  font-size: 14px; font-weight: 600; color: #64ffda;
  padding-bottom: 8px; border-bottom: 1px solid rgba(100,255,218,0.15);
  flex-shrink: 0; display: flex; align-items: center; gap: 6px;
}
.ur-dot { font-size: 10px; }
.ur-sub { font-size: 11px; font-weight: 400; color: #8892b0; }
.ur-badge {
  font-size: 8px; margin-left: auto; padding: 1px 5px; border-radius: 3px;
}
.ur-badge.cumu {
  border: 1px solid #ffd43b; color: #ffd43b;
  background: rgba(255,212,59,0.1);
}

/* ---- 三列 Grid 表头 ---- */
.ur-table-header {
  display: grid;
  grid-template-columns: 50px 1fr 60px;
  gap: 0;
  padding: 6px 0 4px 0;
  font-size: 10px; color: #5a6680; text-transform: uppercase; letter-spacing: 1px;
  flex-shrink: 0;
  border-bottom: 1px dashed rgba(100,255,218,0.08);
}
.ur-table-header .ur-col-medal { text-align: center; }
.ur-table-header .ur-col-name  { text-align: left; padding-left: 4px; }
.ur-table-header .ur-col-count { text-align: right; padding-right: 4px; }

/* ---- 排行列表（填满卡片） ---- */
.ur-list {
  flex: 1; min-height: 0;
  overflow-y: auto;
  display: flex; flex-direction: column;
}

/* ---- 每行：flex:1 均匀分布，三列 Grid ---- */
.ur-row {
  display: grid;
  grid-template-columns: 50px 1fr 60px;
  gap: 0;
  align-items: center;
  /* 核心：每行等分剩余高度，10条均匀填满 */
  flex: 1 1 0;
  min-height: 0;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background 0.2s;
}
.ur-row:hover {
  background: rgba(100,255,218,0.04);
}
.ur-row.ur-top3 {
  background: rgba(100,255,218,0.02);
}
.ur-row.ur-top3:hover {
  background: rgba(100,255,218,0.06);
}

/* ---- 奖牌列（50px 固定，水平居中） ---- */
.ur-col-medal {
  width: 50px;
  text-align: center;
  flex-shrink: 0;
}
.ur-medal {
  font-size: 16px;
  display: inline-block;
  /* 固定奖牌位置，不随任何内容移动 */
}
.medal-gold   { filter: drop-shadow(0 0 4px rgba(255,215,0,0.5)); }
.medal-silver { filter: drop-shadow(0 0 4px rgba(192,192,192,0.4)); }
.medal-bronze { filter: drop-shadow(0 0 4px rgba(205,127,50,0.4)); }
.ur-rank-num {
  font-size: 11px; color: #5a6680;
  font-family: 'Consolas', 'Courier New', monospace;
  font-weight: 700;
}

/* ---- 用户名列（1fr 自适应，左对齐，省略号） ---- */
.ur-col-name {
  text-align: left;
  padding-left: 4px;
  font-size: 12px; font-weight: 600; color: #e0e6ff;
  /* 关键：不换行 + 省略号 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}
/* 前三名用户名高亮 */
.ur-row.ur-top3 .ur-col-name {
  color: #ffffff;
}

/* ---- 发言次数列（60px 固定，右对齐） ---- */
.ur-col-count {
  width: 60px;
  text-align: right;
  padding-right: 4px;
  font-size: 13px; font-weight: 700; color: #64ffda;
  font-family: 'Consolas', 'Courier New', monospace;
  flex-shrink: 0;
}

/* ---- 空状态 ---- */
.ur-empty {
  flex: 1; display: flex; align-items: center; justify-content: center;
  color: #5a6680; font-size: 12px;
}
</style>
