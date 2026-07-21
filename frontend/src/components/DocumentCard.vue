<template>
  <div class="doc-card">
    <div class="info">
      <h3>{{ doc.title }}</h3>
      <span class="meta">{{ doc.source_type === 'upload' ? '文件' : '粘贴' }} · {{ doc.quiz_count }} 份题目</span>
    </div>
    <div class="actions">
      <button @click="$emit('generate', doc)" class="btn-primary">生成题目</button>
      <button @click="$emit('delete', doc)" class="btn-danger">删除</button>
    </div>
  </div>
</template>

<script setup>
defineProps({ doc: Object })
defineEmits(['generate', 'delete'])
</script>

<style scoped>
.doc-card {
  display: flex; justify-content: space-between; align-items: center;
  padding: 15px; background: white; border-radius: 8px; margin-bottom: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.info h3 { font-size: 16px; margin-bottom: 4px; }
.meta { font-size: 12px; color: #999; }
.actions { display: flex; gap: 8px; }
.btn-primary { padding: 8px 16px; background: #1a73e8; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-primary:hover { background: #1557b0; }
.btn-danger { padding: 8px 16px; background: #fff; color: #d93025; border: 1px solid #d93025; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-danger:hover { background: #fce8e6; }
</style>
