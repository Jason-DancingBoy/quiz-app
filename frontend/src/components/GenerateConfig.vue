<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h3>生成题目 — {{ doc.title }}</h3>

      <label>难易度</label>
      <select v-model="difficulty">
        <option value="easy">简单</option>
        <option value="medium" selected>中等</option>
        <option value="hard">困难</option>
      </select>

      <label>题目数量</label>
      <select v-model="questionCount">
        <option :value="5">5 道</option>
        <option :value="10" selected>10 道</option>
        <option :value="15">15 道</option>
        <option :value="20">20 道</option>
      </select>

      <div class="modal-actions">
        <button @click="$emit('close')" class="btn-cancel">取消</button>
        <button @click="confirm" :disabled="loading" class="btn-primary">
          {{ loading ? '生成中...' : '开始生成' }}
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({ doc: Object, api: Object })
const emit = defineEmits(['close', 'generated'])

const difficulty = ref('medium')
const questionCount = ref(10)
const loading = ref(false)
const error = ref('')

async function confirm() {
  loading.value = true
  error.value = ''
  try {
    const result = await props.api.generate(props.doc.id, difficulty.value, questionCount.value)
    emit('generated', result.id)
  } catch (e) {
    error.value = e.message
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: white; padding: 30px; border-radius: 12px; width: 400px; max-width: 90%; }
.modal h3 { margin-bottom: 20px; }
label { display: block; margin: 12px 0 4px; font-size: 14px; color: #666; }
select { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; }
.btn-cancel { padding: 8px 20px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; }
.btn-primary { padding: 8px 20px; background: #1a73e8; color: white; border: none; border-radius: 6px; cursor: pointer; }
.btn-primary:disabled { background: #93b8f0; cursor: not-allowed; }
.error { color: #d93025; margin-top: 12px; font-size: 13px; }
</style>
