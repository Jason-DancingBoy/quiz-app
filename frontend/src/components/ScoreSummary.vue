<template>
  <div class="score-summary" :class="score >= total / 2 ? 'good' : 'bad'">
    <div class="score-icon">
      <svg v-if="score >= total * 0.8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
      <svg v-else-if="score >= total * 0.6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48">
        <circle cx="12" cy="12" r="10"/>
        <line x1="8" y1="15" x2="16" y2="15"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48">
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
    </div>
    <div class="score-circle">
      <span class="score-num">{{ score }}</span>
      <span class="score-div">/ {{ total }}</span>
    </div>
    <p class="score-msg">
      {{ score >= total * 0.8 ? '太棒了，掌握得很扎实！' : score >= total * 0.6 ? '不错，继续加油！' : '再加把劲，你可以的！' }}
    </p>
  </div>
</template>

<script setup>
defineProps({ score: Number, total: Number })
</script>

<style scoped>
.score-summary {
  text-align: center;
  padding: var(--space-8);
  border-radius: var(--radius-xl);
  margin-bottom: var(--space-8);
  transition: all var(--transition-base);
}

.score-summary.good {
  background: linear-gradient(135deg, var(--color-success-bg), var(--color-primary-bg));
  border: 1px solid var(--color-success-border);
}

.score-summary.bad {
  background: linear-gradient(135deg, var(--color-error-bg), #FFF7ED);
  border: 1px solid var(--color-error-border);
}

.score-icon {
  margin-bottom: var(--space-4);
}

.good .score-icon {
  color: var(--color-success);
}

.bad .score-icon {
  color: var(--color-error);
}

.score-circle {
  margin-bottom: var(--space-3);
}

.score-num {
  font-family: var(--font-heading);
  font-size: 56px;
  font-weight: 700;
  line-height: 1;
}

.good .score-num { color: var(--color-primary-dark); }
.bad .score-num { color: var(--color-error); }

.score-div {
  font-size: var(--text-xl);
  color: var(--color-text-muted);
}

.score-msg {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--color-text-secondary);
}
</style>
