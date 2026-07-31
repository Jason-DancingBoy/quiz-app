<template>
  <div>
    <DocumentInput :api="api" @created="loadDocs" />

    <div class="vault-card card">
      <div class="vault-info">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="28" height="28">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          <line x1="8" y1="7" x2="16" y2="7"/>
          <line x1="8" y1="11" x2="14" y2="11"/>
        </svg>
        <div>
          <h3>Vault 笔记库</h3>
          <span class="vault-meta">Obsidian 学习笔记</span>
        </div>
      </div>
      <button class="btn-primary" @click="showConfig = { id: 'vault', title: 'Vault 笔记库' }">
        生成题目
      </button>
    </div>

    <div class="doc-list" v-if="docs.length">
      <DocumentCard
        v-for="doc in docs" :key="doc.id" :doc="doc"
        @view="showContent = doc"
        @generate="showConfig = doc"
        @delete="handleDelete(doc)"
      />
    </div>
    <div v-else class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <p>暂无文档，粘贴或上传一篇开始刷题</p>
    </div>

    <GenerateConfig
      v-if="showConfig" :doc="showConfig" :api="api"
      @close="showConfig = null"
      @generated="onGenerated"
    />

    <div v-if="contentDoc" class="modal-overlay" @click.self="contentDoc = null">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ contentDoc.title }}</h2>
          <button class="close-btn" @click="contentDoc = null">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="contentDoc.content" class="doc-content md-content" v-html="renderMarkdown(contentDoc.content)"></div>
          <p v-else class="loading-text">加载中...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { renderMarkdown } from '../markdown'
import DocumentInput from '../components/DocumentInput.vue'
import DocumentCard from '../components/DocumentCard.vue'
import GenerateConfig from '../components/GenerateConfig.vue'

const docs = ref([])
const showConfig = ref(null)
const showContent = ref(null)
const contentDoc = ref(null)
const router = useRouter()

async function loadDocs() {
  docs.value = await api.listDocuments()
}

async function handleDelete(doc) {
  if (!confirm(`确定删除「${doc.title}」？`)) return
  await api.deleteDocument(doc.id)
  await loadDocs()
}

function onGenerated(quizId) {
  showConfig.value = null
  router.push(`/quiz/${quizId}`)
}

watch(showContent, async (doc) => {
  if (doc) {
    contentDoc.value = { title: doc.title, content: null }
    const detail = await api.getDocument(doc.id)
    contentDoc.value = detail
  } else {
    contentDoc.value = null
  }
})

onMounted(loadDocs)
</script>

<style scoped>
.vault-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-5);
  margin-bottom: var(--space-4);
  gap: var(--space-4);
  border-left: 3px solid var(--color-primary);
}

.vault-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.vault-info svg {
  color: var(--color-primary);
  flex-shrink: 0;
}

.vault-info h3 {
  font-family: var(--font-heading);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
}

.vault-meta {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: var(--space-4);
}

.modal-content {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 720px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border-light);
}

.modal-header h2 {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: var(--space-4);
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: 4px;
  border-radius: var(--radius-sm);
  min-height: 32px;
  min-width: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.close-btn:hover {
  color: var(--color-text);
  background: var(--color-border-light);
}

.modal-body {
  padding: var(--space-6);
  overflow-y: auto;
  flex: 1;
}

.doc-content {
  font-size: var(--text-sm);
  line-height: 1.8;
  color: var(--color-text);
}

.doc-content :deep(p) { margin-bottom: var(--space-3); }
.doc-content :deep(strong) { font-weight: 600; }
.doc-content :deep(em) { font-style: italic; }
.doc-content :deep(code) {
  background: var(--color-bg);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.875em;
}
.doc-content :deep(pre) {
  background: var(--color-bg);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin-bottom: var(--space-3);
}
.doc-content :deep(pre code) {
  background: none;
  padding: 0;
}
.doc-content :deep(ul), .doc-content :deep(ol) {
  padding-left: var(--space-6);
  margin-bottom: var(--space-3);
}
.doc-content :deep(li) { margin-bottom: var(--space-1); }
.doc-content :deep(blockquote) {
  border-left: 3px solid var(--color-primary-border);
  padding-left: var(--space-4);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-3);
}
.doc-content :deep(h1), .doc-content :deep(h2), .doc-content :deep(h3) {
  font-family: var(--font-heading);
  font-weight: 600;
  margin: var(--space-4) 0 var(--space-2);
}
.doc-content :deep(h1) { font-size: var(--text-xl); }
.doc-content :deep(h2) { font-size: var(--text-lg); }
.doc-content :deep(h3) { font-size: var(--text-base); }
.doc-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: var(--space-3);
}
.doc-content :deep(th), .doc-content :deep(td) {
  border: 1px solid var(--color-border-light);
  padding: var(--space-2) var(--space-3);
  text-align: left;
}
.doc-content :deep(th) {
  background: var(--color-bg);
  font-weight: 600;
}

.loading-text {
  text-align: center;
  color: var(--color-text-muted);
  padding: var(--space-8);
}
</style>
