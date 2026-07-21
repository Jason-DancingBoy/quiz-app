<template>
  <div class="quiz-page">
    <div v-if="loading" class="status-box">
      <div class="spinner"></div>
      <p>{{ progress || '加载中...' }}</p>
    </div>

    <div v-else-if="quizData && !submitted">
      <ProgressBar :current="currentIndex + 1" :total="quizData.total" />
      <QuestionCard
        :question="quizData.questions[currentIndex]"
        :selected="answers[quizData.questions[currentIndex].id]"
        @select="(idx) => selectAnswer(quizData.questions[currentIndex].id, idx)"
      />
      <div class="nav-buttons">
        <button v-if="currentIndex > 0" @click="currentIndex--" class="btn-secondary">上一题</button>
        <button v-if="currentIndex < quizData.total - 1" @click="currentIndex++" class="btn-primary" :disabled="answers[quizData.questions[currentIndex].id] === undefined">下一题</button>
        <button v-if="currentIndex === quizData.total - 1" @click="handleSubmit" class="btn-submit" :disabled="!allAnswered || submitting">
          {{ submitting ? '提交中...' : '提交全部答案' }}
        </button>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import ProgressBar from '../components/ProgressBar.vue'
import QuestionCard from '../components/QuestionCard.vue'

const props = defineProps({ id: String })
const router = useRouter()

const loading = ref(true)
const progress = ref('')
const quizData = ref(null)
const currentIndex = ref(0)
const answers = reactive({})
const submitted = ref(false)
const submitting = ref(false)
const error = ref('')

const allAnswered = computed(() => {
  if (!quizData.value) return false
  return quizData.value.questions.every(q => answers[q.id] !== undefined)
})

function selectAnswer(questionId, index) {
  answers[questionId] = index
}

let pollTimer = null

async function pollQuiz() {
  try {
    const data = await api.getQuiz(parseInt(props.id))
    if (data.status === 'generating') {
      progress.value = data.progress || '生成中...'
    } else if (data.status === 'ready') {
      loading.value = false
      quizData.value = data
      clearInterval(pollTimer)
    } else if (data.status === 'failed') {
      error.value = data.progress || '生成失败'
      loading.value = false
      clearInterval(pollTimer)
    }
  } catch (e) {
    error.value = e.message
    loading.value = false
    clearInterval(pollTimer)
  }
}

onMounted(() => {
  pollQuiz()
  pollTimer = setInterval(pollQuiz, 1000)
})

async function handleSubmit() {
  submitting.value = true
  error.value = ''
  try {
    const answerList = Object.entries(answers).map(([qid, idx]) => ({
      question_id: parseInt(qid),
      selected_index: idx,
    }))
    const result = await api.submitQuiz(parseInt(props.id), answerList)
    submitted.value = true
    router.push(`/quiz/${props.id}/review`)
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>
