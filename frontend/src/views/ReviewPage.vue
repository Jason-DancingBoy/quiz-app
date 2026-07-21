<template>
  <div class="review-page">
    <div v-if="loading" class="status-box">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="reviewData">
      <ScoreSummary :score="reviewData.score" :total="reviewData.total" />
      <ReviewItem
        v-for="item in reviewData.answers"
        :key="item.question_id"
        :item="item"
      />
      <div class="review-actions">
        <button @click="$router.push('/')" class="btn-primary">返回首页</button>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import ScoreSummary from '../components/ScoreSummary.vue'
import ReviewItem from '../components/ReviewItem.vue'

const props = defineProps({ id: String })

const loading = ref(true)
const reviewData = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    reviewData.value = await api.getReview(parseInt(props.id))
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>
