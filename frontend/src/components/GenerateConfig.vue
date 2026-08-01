<template>
  <div class="modal-overlay" @click.self="$emit('close')" @keydown.escape="$emit('close')">
    <div class="modal card" role="dialog" aria-labelledby="modal-title">
      <div class="modal-header">
        <h3 id="modal-title">生成题目</h3>
        <p class="modal-subtitle">「{{ doc.title }}」</p>
      </div>

      <div class="field">
        <label for="difficulty">难易度</label>
        <select id="difficulty" v-model="difficulty" class="select">
          <option value="easy">简单</option>
          <option value="medium">中等</option>
          <option value="hard">困难</option>
        </select>
      </div>

      <div class="field">
        <label for="question-count">题目数量</label>
        <select id="question-count" v-model="questionCount" class="select">
          <option :value="5">5 道</option>
          <option :value="10">10 道</option>
          <option :value="15">15 道</option>
          <option :value="20">20 道</option>
        </select>
      </div>

      <div class="modal-actions">
        <button @click="$emit('close')" class="btn-secondary">取消</button>
        <button @click="confirm" :disabled="loading" class="btn-primary">
          <svg v-if="loading" class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
          {{ loading ? '生成中...' : '开始生成' }}
        </button>
      </div>

      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
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
    const isVault = props.doc.id === 'vault'
    const result = isVault
      ? await props.api.vaultGenerate(difficulty.value, questionCount.value)
      : await props.api.generate(props.doc.id, difficulty.value, questionCount.value)
    emit('generated', result.id)
  } catch (e) {
    error.value = e.message
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 30, 28, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: var(--space-4);
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal {
  background: var(--color-surface);
  padding: var(--space-8);
  border-radius: var(--radius-xl);
  width: 420px;
  max-width: 100%;
  animation: slideUp 0.25s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(16px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  margin-bottom: var(--space-6);
}

.modal-header h3 {
  font-family: var(--font-heading);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 2px;
}

.modal-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.field {
  margin-bottom: var(--space-4);
}

.field label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: var(--space-2);
}

.select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  color: var(--color-text);
  background: var(--color-surface);
  cursor: pointer;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  min-height: 44px;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%235F7370' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  padding-right: 36px;
}

.select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-6);
}

.spin-icon {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
