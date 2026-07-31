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
        <button @click="$router.push('/')" class="btn-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          </svg>
          返回首页
        </button>
      </div>
    </div>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
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

<style scoped>
.review-actions {
  text-align: center;
  margin-top: var(--space-8);
}
</style>
