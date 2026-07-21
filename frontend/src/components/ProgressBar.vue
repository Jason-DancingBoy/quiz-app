<template>
  <div class="progress-bar">
    <div class="progress-fill" :style="{ width: (current / total * 100) + '%' }"></div>
    <span class="progress-text">{{ current }} / {{ total }}</span>
  </div>
</template>

<script setup>
defineProps({ current: Number, total: Number })
</script>

<style scoped>
.progress-bar { height: 6px; background: #e0e0e0; border-radius: 3px; margin-bottom: 24px; position: relative; }
.progress-fill { height: 100%; background: #1a73e8; border-radius: 3px; transition: width 0.3s; }
.progress-text { position: absolute; top: -20px; right: 0; font-size: 13px; color: #666; }
</style>
