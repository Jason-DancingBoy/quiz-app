<template>
  <div class="progress-wrap">
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: (current / total * 100) + '%' }"></div>
    </div>
    <span class="progress-text">{{ current }} / {{ total }}</span>
  </div>
</template>

<script setup>
defineProps({ current: Number, total: Number })
</script>

<style scoped>
.progress-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
  border-radius: var(--radius-full);
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-text {
  flex-shrink: 0;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
  min-width: 3em;
  text-align: right;
}
</style>
