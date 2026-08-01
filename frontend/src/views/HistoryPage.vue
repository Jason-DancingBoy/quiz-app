<template>
  <div class="history-page">
    <div class="page-header">
      <h2>历史记录</h2>
      <span v-if="items.length" class="count-badge">{{ items.length }}</span>
    </div>

    <div v-if="items.length">
      <router-link
        v-for="item in items"
        :key="item.id"
        :to="item.score !== null ? `/quiz/${item.id}/review` : `/quiz/${item.id}`"
        class="history-item card"
      >
        <div class="h-left">
          <svg class="h-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <div class="h-info">
            <strong>{{ item.document_title }}</strong>
            <span class="h-meta">
              {{ item.difficulty === 'easy' ? '简单' : item.difficulty === 'hard' ? '困难' : '中等' }}
              <span class="dot">·</span>
              {{ item.total }} 题
            </span>
          </div>
        </div>
        <div class="h-right">
          <span v-if="item.score !== null" class="score">{{ item.score }}/{{ item.total }}</span>
          <span v-else class="pending">未完成</span>
          <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </div>
      </router-link>
    </div>

    <div v-else class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
      <p>还没有做题记录</p>
      <p class="empty-hint">去首页创建文档并生成题目吧</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const items = ref([])

onMounted(async () => {
  items.value = await api.listQuizzes()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-family: var(--font-heading);
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
}

.count-badge {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-primary-dark);
  background: var(--color-primary-bg);
  padding: 2px 10px;
  border-radius: var(--radius-full);
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  margin-bottom: var(--space-3);
  text-decoration: none;
  gap: var(--space-4);
}

.h-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.h-icon {
  flex-shrink: 0;
  color: var(--color-primary);
}

.h-info {
  min-width: 0;
}

.h-info strong {
  display: block;
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.h-meta {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}

.dot {
  color: var(--color-border);
}

.h-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

.score {
  font-weight: 700;
  font-size: var(--text-base);
  color: var(--color-primary-dark);
  font-variant-numeric: tabular-nums;
}

.pending {
  font-size: var(--text-xs);
  color: var(--color-accent);
  background: var(--color-accent-light);
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-weight: 500;
}

.chevron {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.empty-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
}
</style>
