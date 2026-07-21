<template>
  <div class="doc-input">
    <div class="tabs">
      <button :class="{ active: mode === 'paste' }" @click="mode = 'paste'">粘贴文本</button>
      <button :class="{ active: mode === 'upload' }" @click="mode = 'upload'">上传文件</button>
    </div>

    <div v-if="mode === 'paste'" class="paste-area">
      <input v-model="title" placeholder="文档标题（可选）" class="title-input" />
      <textarea v-model="content" placeholder="粘贴文档内容..." rows="8"></textarea>
      <button @click="submitPaste" :disabled="!content.trim() || loading" class="btn-primary">
        {{ loading ? '提交中...' : '提交文档' }}
      </button>
    </div>

    <div v-else class="upload-area">
      <input type="file" ref="fileInput" accept=".pdf,.docx,.md,.txt" @change="submitUpload" />
      <p class="hint">支持 PDF / Word / Markdown / TXT，最大 10MB</p>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
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
  error.value = ''
  emit('created')
}
</script>
