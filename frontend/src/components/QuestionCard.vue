<template>
  <div class="question-card">
    <h3>{{ question.order_num }}. {{ question.content }}</h3>
    <div
      v-for="(option, i) in question.options"
      :key="i"
      :class="['option', { selected: selected === i }]"
      @click="$emit('select', i)"
    >
      <span class="option-letter">{{ ['A','B','C','D'][i] }}</span>
      <span class="option-text">{{ option }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({ question: Object, selected: Number })
defineEmits(['select'])
</script>

<style scoped>
.question-card { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.question-card h3 { font-size: 17px; line-height: 1.6; margin-bottom: 20px; }
.option { display: flex; align-items: flex-start; padding: 12px 16px; margin-bottom: 8px; border: 2px solid #e8e8e8; border-radius: 8px; cursor: pointer; transition: border-color 0.2s; }
.option:hover { border-color: #1a73e8; }
.option.selected { border-color: #1a73e8; background: #e8f0fe; }
.option-letter { width: 28px; height: 28px; border-radius: 50%; background: #f0f0f0; display: flex; align-items: center; justify-content: center; font-weight: 600; margin-right: 12px; flex-shrink: 0; }
.option.selected .option-letter { background: #1a73e8; color: white; }
.option-text { line-height: 1.5; padding-top: 3px; }
</style>
