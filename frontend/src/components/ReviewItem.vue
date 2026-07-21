<template>
  <div class="review-item" :class="item.is_correct ? 'correct' : 'wrong'">
    <div class="review-header">
      <span class="icon">{{ item.is_correct ? 'correct' : 'wrong' }}</span>
      <span class="result-text">
        {{ item.is_correct ? '正确' : '错误' }} —
        你选了 {{ ['A','B','C','D'][item.selected_index] }}，
        正确答案 {{ ['A','B','C','D'][item.correct_index] }}
      </span>
    </div>
    <div class="explanation">{{ item.explanation }}</div>
  </div>
</template>

<script setup>
defineProps({ item: Object })
</script>

<style scoped>
.review-item { padding: 16px; border-radius: 8px; margin-bottom: 12px; }
.review-item.correct { background: #e6f4ea; border-left: 4px solid #1e8e3e; }
.review-item.wrong { background: #fce8e6; border-left: 4px solid #d93025; }
.review-header { margin-bottom: 8px; font-size: 14px; }
.icon { margin-right: 8px; }
.explanation { font-size: 14px; line-height: 1.6; color: #555; }
</style>
