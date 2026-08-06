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
      <a
        :href="'/api/documents/' + doc.id + '/download'"
        download
        class="btn-icon"
        title="下载"
        aria-label="下载"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
      </a>
      <button
        @click="$emit('view', doc)"
        class="btn-icon"
        title="查看内容"
        aria-label="查看内容"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
          <circle cx="12" cy="12" r="3"/>
        </svg>
      </button>
      <button @click="$emit('generate', doc)" class="btn-primary">生成题目</button>
      <button
        @click="$emit('delete', doc)"
        class="btn-icon btn-icon-danger"
        title="删除"
        aria-label="删除"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          <line x1="10" y1="11" x2="10" y2="17"/>
          <line x1="14" y1="11" x2="14" y2="17"/>
        </svg>
      </button>
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

.actions .btn-primary {
  padding: 8px 16px;
  font-size: var(--text-sm);
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: 6px;
  border-radius: var(--radius-sm);
  min-height: 32px;
  min-width: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.btn-icon:hover {
  color: var(--color-text);
  background: var(--color-border-light);
}

.btn-icon-danger:hover {
  color: var(--color-destructive);
  background: var(--color-error-bg);
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
