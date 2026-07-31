<template>
  <div class="review-item" :class="item.is_correct ? 'correct' : 'wrong'">
    <p class="question-text md-content" v-html="renderMarkdown(item.content)"></p>
    <div class="options-list">
      <div
        v-for="(opt, idx) in item.options"
        :key="idx"
        class="option"
        :class="{
          selected: idx === item.selected_index,
          correct: idx === item.correct_index,
        }"
      >
        <span class="option-letter">{{ ['A','B','C','D'][idx] }}.</span>
        <span class="md-content" v-html="renderMarkdown(opt)"></span>
      </div>
    </div>
    <div class="review-header">
      <svg v-if="item.is_correct" class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="22" height="22">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
      <svg v-else class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="22" height="22">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
      <span class="result-text">
        <strong>{{ item.is_correct ? '正确' : '错误' }}</strong>
        — 你选了 {{ ['A','B','C','D'][item.selected_index] }}，
        正确答案 {{ ['A','B','C','D'][item.correct_index] }}
      </span>
    </div>
    <div class="explanation md-content" v-html="renderMarkdown(item.explanation)"></div>
  </div>
</template>

<script setup>
import { renderMarkdown } from '../markdown'

defineProps({ item: Object })
</script>

<style scoped>
.question-text {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-3);
  line-height: 1.6;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.option {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  line-height: 1.5;
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
}

.option.selected {
  border-color: var(--color-accent);
  background: var(--color-accent-light);
}

.option.correct {
  border-color: var(--color-success);
  background: var(--color-success-bg);
}

.option.selected.correct {
  border-color: var(--color-success);
  background: var(--color-success-bg);
}

.option-letter {
  font-weight: 700;
  margin-right: var(--space-1);
}

.review-item {
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-3);
  border: 1px solid transparent;
  transition: all var(--transition-fast);
}

.review-item.correct {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
}

.review-item.wrong {
  background: var(--color-error-bg);
  border-color: var(--color-error-border);
}

.review-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.status-icon {
  flex-shrink: 0;
}

.review-item.correct .status-icon {
  color: var(--color-success);
}

.review-item.wrong .status-icon {
  color: var(--color-error);
}

.result-text {
  font-size: var(--text-sm);
  color: var(--color-text);
  line-height: 1.5;
}

.result-text strong {
  font-weight: 600;
}

.explanation {
  font-size: var(--text-sm);
  line-height: 1.7;
  color: var(--color-text-secondary);
  padding: var(--space-3);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
}
</style>
