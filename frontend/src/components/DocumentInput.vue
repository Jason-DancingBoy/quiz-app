<template>
  <div class="doc-input card">
    <div class="tabs">
      <button
        :class="['tab', { active: mode === 'paste' }]"
        @click="mode = 'paste'"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
          <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
          <rect x="8" y="2" width="8" height="4" rx="1"/>
        </svg>
        粘贴文本
      </button>
      <button
        :class="['tab', { active: mode === 'upload' }]"
        @click="mode = 'upload'"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        上传文件
      </button>
    </div>

    <div v-if="mode === 'paste'" class="paste-area">
      <div class="field">
        <label for="doc-title">文档标题</label>
        <input
          id="doc-title"
          v-model="title"
          placeholder="输入标题，方便后续查找..."
          class="input"
        />
      </div>
      <div class="field">
        <label for="doc-content">文档内容</label>
        <textarea
          id="doc-content"
          v-model="content"
          placeholder="粘贴文档内容，AI 会自动生成题目..."
          rows="8"
          class="textarea"
        ></textarea>
      </div>
      <button
        @click="submitPaste"
        :disabled="!content.trim() || loading"
        class="btn-primary btn-full"
      >
        <svg v-if="loading" class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        {{ loading ? '提交中...' : '提交文档' }}
      </button>
    </div>

    <div v-else class="upload-area">
      <div v-if="loading" class="upload-dropzone uploading">
        <svg class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="40" height="40">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        <p>上传中...</p>
      </div>
      <div v-else class="upload-dropzone">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        <label class="file-label" for="file-upload">选择文件</label>
        <input
          id="file-upload"
          ref="fileInput"
          type="file"
          accept=".pdf,.docx,.pptx,.md,.txt"
          @change="submitUpload"
          class="file-input"
        />
        <p class="hint">支持 PDF / Word / PPT / Markdown / TXT，最大 100MB</p>
      </div>
    </div>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['created'])
const mode = ref('paste')
const title = ref('')
const content = ref('')
const loading = ref(false)
const error = ref('')
const fileInput = ref(null)
const props = defineProps({ api: Object })

async function submitPaste() {
  loading.value = true
  error.value = ''
  try {
    await props.api.createDocument(title.value || 'Untitled', content.value)
    title.value = ''
    content.value = ''
    emit('created')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function submitUpload() {
  const input = fileInput.value
  const file = input?.files?.[0]
  if (!file) return

  loading.value = true
  error.value = ''
  try {
    await props.api.uploadDocument(file)
    input.value = ''
    emit('created')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.doc-input {
  padding: var(--space-6);
  margin-bottom: var(--space-8);
}

/* Tabs */
.tabs {
  display: flex;
  gap: var(--space-1);
  background: var(--color-border-light);
  padding: 4px;
  border-radius: var(--radius-md);
  margin-bottom: var(--space-5);
}

.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  min-height: 40px;
}

.tab:hover {
  color: var(--color-text);
}

.tab.active {
  background: var(--color-surface);
  color: var(--color-primary-dark);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.tab svg {
  flex-shrink: 0;
}

/* Fields */
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

.input,
.textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  color: var(--color-text);
  background: var(--color-surface);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  min-height: 44px;
}

.input:focus,
.textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15);
}

.input::placeholder,
.textarea::placeholder {
  color: var(--color-text-muted);
}

.textarea {
  resize: vertical;
  line-height: 1.6;
}

.btn-full {
  width: 100%;
  margin-top: var(--space-2);
}

/* Upload */
.upload-dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-8) var(--space-4);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.upload-dropzone:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-bg);
}

.upload-dropzone.uploading {
  border-color: var(--color-primary);
  background: var(--color-primary-bg);
}

.file-label {
  padding: 8px 20px;
  background: var(--color-primary-bg);
  color: var(--color-primary-dark);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-fast);
  min-height: 40px;
  display: flex;
  align-items: center;
}

.file-label:hover {
  background: var(--color-primary-border);
}

.file-input {
  position: absolute;
  width: 0.1px;
  height: 0.1px;
  opacity: 0;
  overflow: hidden;
}

.hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.spin-icon {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
