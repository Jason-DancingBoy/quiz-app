<template>
  <div>
    <h2>历史记录</h2>
    <div v-if="items.length">
      <div v-for="item in items" :key="item.id" class="history-item">
        <div class="h-info">
          <strong>{{ item.document_title }}</strong>
          <span class="h-meta">{{ item.difficulty === 'easy' ? '简单' : item.difficulty === 'hard' ? '困难' : '中等' }} · {{ item.total }} 题</span>
        </div>
        <div class="h-score">
          <span v-if="item.score !== null" class="score">{{ item.score }}/{{ item.total }}</span>
          <span v-else class="pending">未完成</span>
        </div>
      </div>
    </div>
    <p v-else class="empty">还没有做题记录</p>
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
