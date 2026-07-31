<template>
  <div class="quiz-page">
    <div v-if="loading || generatingMore" class="generation-progress">
      <ProgressBar
        :current="quizData?.questions?.length || 0"
        :total="quizData?.total || totalCount || 1"
      />
      <div class="generation-status">
        <div class="spinner-sm"></div>
        <span>{{ stageMessage || progress || '准备中...' }}</span>
      </div>
    </div>

    <div v-if="quizData && !submitted">
      <ProgressBar :current="currentIndex + 1" :total="quizData.total" />
      <QuestionCard
        :question="quizData.questions[currentIndex]"
        :selected="answers[quizData.questions[currentIndex].id]"
        @select="(idx) => selectAnswer(quizData.questions[currentIndex].id, idx)"
      />
      <div class="nav-buttons">
        <button v-if="currentIndex > 0" @click="currentIndex--" class="btn-secondary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          上一题
        </button>
        <div class="nav-spacer"></div>
        <button
          v-if="currentIndex < quizData.questions.length - 1"
          @click="currentIndex++"
          class="btn-primary"
          :disabled="answers[quizData.questions[currentIndex].id] === undefined"
        >
          下一题
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
        <button
          v-if="currentIndex === quizData.questions.length - 1 && !generatingMore"
          @click="handleSubmit"
          class="btn-submit"
          :disabled="!allAnswered || submitting"
        >
          <svg v-if="submitting" class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
          {{ submitting ? '提交中...' : '提交全部答案' }}
        </button>
      </div>
    </div>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import ProgressBar from '../components/ProgressBar.vue'
import QuestionCard from '../components/QuestionCard.vue'

const props = defineProps({ id: String })
const router = useRouter()

const loading = ref(true)
const progress = ref('')
const stageMessage = ref('')
const totalCount = ref(0)
const quizData = ref(null)
const currentIndex = ref(0)
const answers = reactive({})
const submitted = ref(false)
const submitting = ref(false)
const error = ref('')
const generatingMore = ref(false)

const allAnswered = computed(() => {
  if (!quizData.value) return false
  return quizData.value.questions.every(q => answers[q.id] !== undefined)
})

function selectAnswer(questionId, index) {
  answers[questionId] = index
}

let eventSource = null
let pollTimer = null

async function pollQuiz() {
  try {
    const data = await api.getQuiz(parseInt(props.id))
    if (data.status === 'generating') {
      if (data.questions && data.questions.length > 0) {
        quizData.value = { id: data.id, total: data.total_count, questions: data.questions }
        generatingMore.value = true
        loading.value = false
        progress.value = data.progress || '生成中...'
      } else {
        progress.value = data.progress || '生成中...'
      }
    } else if (data.status === 'ready') {
      if (data.submitted) {
        router.replace(`/quiz/${props.id}/review`)
        return
      }
      generatingMore.value = false
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

function connectSSE() {
  const quizId = parseInt(props.id)
  eventSource = new EventSource(`/api/quizzes/${quizId}/stream`)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'progress') {
        stageMessage.value = data.message
        totalCount.value = data.total_count

      } else if (data.type === 'question') {
        totalCount.value = data.total_count

        // Add question if not already present
        if (!quizData.value) {
          quizData.value = {
            id: quizId,
            total: data.total_count,
            questions: [],
          }
        }
        // Update total in case it changed
        quizData.value.total = data.total_count

        const exists = quizData.value.questions.find(q => q.id === data.question.id)
        if (!exists) {
          quizData.value.questions.push(data.question)
        }

        loading.value = false
        generatingMore.value = true
        stageMessage.value = `已生成 ${quizData.value.questions.length}/${data.total_count} 题...`

      } else if (data.type === 'done') {
        // Generation complete — do a final poll to get full QuizReady data
        generatingMore.value = false
        eventSource.close()
        pollQuiz()

      } else if (data.type === 'error') {
        error.value = data.message || '生成失败'
        loading.value = false
        generatingMore.value = false
        eventSource.close()
      }
    } catch (e) {
      // JSON parse error — ignore malformed events
    }
  }

  eventSource.onerror = () => {
    // Fall back to polling
    eventSource.close()
    generatingMore.value = false
    pollQuiz()
    pollTimer = setInterval(pollQuiz, 1000)
  }
}

onMounted(() => {
  connectSSE()
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
  clearInterval(pollTimer)
})

async function handleSubmit() {
  if (submitting.value || submitted.value) return
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

<style scoped>
.nav-buttons {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.nav-spacer {
  flex: 1;
}

.spin-icon {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.generation-progress {
  margin-bottom: var(--space-6);
}

.generation-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-2);
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.spinner-sm {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent, #1a73e8);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
</style>
