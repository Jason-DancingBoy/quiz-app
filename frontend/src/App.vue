<template>
  <div class="app">
    <header class="app-header">
      <router-link to="/" class="logo">智能刷题</router-link>
      <nav>
        <router-link to="/">文档</router-link>
        <span class="sep">|</span>
        <router-link to="/history">历史</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; color: #333; }
.app { max-width: 800px; margin: 0 auto; padding: 20px; }
.app-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid #e0e0e0; }
.app-header .logo { font-size: 22px; font-weight: 700; text-decoration: none; color: #1a73e8; }
.app-header nav a { color: #555; text-decoration: none; font-size: 14px; }
.app-header nav a:hover { color: #1a73e8; }
.app-header nav .sep { margin: 0 8px; color: #ccc; }
.app-main { min-height: 400px; }
</style>
