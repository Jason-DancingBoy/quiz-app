<template>
  <div>
    <DocumentInput :api="api" @created="loadDocs" />
    <div class="doc-list" v-if="docs.length">
      <DocumentCard
        v-for="doc in docs" :key="doc.id" :doc="doc"
        @generate="showConfig = doc"
        @delete="handleDelete(doc)"
      />
    </div>
    <p v-else class="empty">暂无文档，粘贴或上传一篇开始刷题</p>

    <GenerateConfig
      v-if="showConfig" :doc="showConfig" :api="api"
      @close="showConfig = null"
      @generated="onGenerated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import DocumentInput from '../components/DocumentInput.vue'
import DocumentCard from '../components/DocumentCard.vue'
import GenerateConfig from '../components/GenerateConfig.vue'

const docs = ref([])
const showConfig = ref(null)
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

onMounted(loadDocs)
</script>
