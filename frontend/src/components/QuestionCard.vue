<template>
  <div class="question-card card">
    <div class="q-header">
      <span class="q-num">{{ question.order_num }}</span>
      <h3 class="md-content" v-html="renderMarkdown(question.content)"></h3>
    </div>
    <div
      v-for="(option, i) in question.options"
      :key="i"
      :class="['option', { selected: selected === i }]"
      @click="$emit('select', i)"
      role="radio"
      :aria-checked="selected === i"
      tabindex="0"
      @keydown.enter="$emit('select', i)"
      @keydown.space.prevent="$emit('select', i)"
    >
      <span class="option-letter">{{ ['A','B','C','D'][i] }}</span>
      <span class="option-text md-content" v-html="renderMarkdown(option)"></span>
      <svg v-if="selected === i" class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="20" height="20">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { renderMarkdown } from '../markdown'

defineProps({ question: Object, selected: Number })
defineEmits(['select'])
</script>

<style scoped>
.question-card {
  padding: var(--space-6);
  margin-bottom: var(--space-5);
}

.q-header {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.q-num {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: var(--text-xs);
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.q-header h3 {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 600;
  line-height: 1.7;
  color: var(--color-text);
}

.option {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 14px 16px;
  margin-bottom: var(--space-2);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 48px;
}

.option:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-bg);
}

.option.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-bg);
}

.option-letter {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--color-border-light);
  color: var(--color-text-secondary);
  font-weight: 700;
  font-size: var(--text-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.option.selected .option-letter {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.option-text {
  flex: 1;
  font-size: var(--text-sm);
  line-height: 1.5;
  color: var(--color-text);
}

.check-icon {
  flex-shrink: 0;
  color: var(--color-primary);
}
</style>
