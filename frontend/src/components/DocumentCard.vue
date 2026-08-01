<template>
  <div class="doc-card card">
    <div class="info">
      <div class="title-row">
        <svg class="type-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        <div>
          <h3>{{ doc.title }}</h3>
          <span class="meta">
            {{ doc.source_type === 'upload' ? '文件上传' : '粘贴文本' }}
            <span class="dot">·</span>
            {{ doc.quiz_count }} 份题目
          </span>
        </div>
      </div>
    </div>
    <div class="actions">
      <button @click="$emit('view', doc)" class="btn-outline">查看内容</button>
      <button @click="$emit('generate', doc)" class="btn-primary">生成题目</button>
      <button @click="$emit('delete', doc)" class="btn-danger">删除</button>
    </div>
  </div>
</template>

<script setup>
defineProps({ doc: Object })
defineEmits(['view', 'generate', 'delete'])
</script>

<style scoped>
.doc-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-5);
  margin-bottom: var(--space-3);
  gap: var(--space-4);
}

.title-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.type-icon {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--color-primary);
}

.doc-card h3 {
  font-family: var(--font-heading);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 2px;
  line-height: 1.4;
}

.meta {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}

.dot {
  color: var(--color-border);
}

.actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

.actions .btn-outline {
  padding: 8px 16px;
  font-size: var(--text-sm);
}

.actions .btn-primary {
  padding: 8px 16px;
  font-size: var(--text-sm);
}

.actions .btn-danger {
  padding: 8px 16px;
  font-size: var(--text-sm);
}

@media (max-width: 480px) {
  .doc-card {
    flex-direction: column;
    align-items: stretch;
  }
  .actions {
    justify-content: flex-end;
  }
}
</style>
