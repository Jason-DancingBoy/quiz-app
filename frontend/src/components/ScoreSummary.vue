<template>
  <div class="score-summary" :class="score >= total / 2 ? 'good' : 'bad'">
    <div class="score-circle">
      <span class="score-num">{{ score }}</span>
      <span class="score-div">/ {{ total }}</span>
    </div>
    <p class="score-msg">{{ score >= total * 0.8 ? '太棒了！' : score >= total * 0.6 ? '不错！' : '继续加油！' }}</p>
  </div>
</template>

<script setup>
defineProps({ score: Number, total: Number })
</script>

<style scoped>
.score-summary { text-align: center; padding: 30px; border-radius: 12px; margin-bottom: 24px; }
.score-summary.good { background: #e6f4ea; }
.score-summary.bad { background: #fce8e6; }
.score-circle { margin-bottom: 10px; }
.score-num { font-size: 48px; font-weight: 700; }
.good .score-num { color: #1e8e3e; }
.bad .score-num { color: #d93025; }
.score-div { font-size: 20px; color: #999; }
.score-msg { font-size: 16px; color: #666; }
</style>
