<template>
  <div class="app">
    <header class="app-header">
      <router-link to="/" class="logo">
        <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
        智能刷题
      </router-link>
      <nav>
        <router-link to="/" exact-active-class="nav-active">文档</router-link>
        <router-link to="/history" active-class="nav-active">历史</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
</script>

<style>
/* ===== Google Fonts ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ===== Design Tokens ===== */
:root {
  /* Colors — Teal palette */
  --color-primary: #0D9488;
  --color-primary-light: #14B8A6;
  --color-primary-dark: #0F766E;
  --color-primary-bg: #F0FDFA;
  --color-primary-border: #99F6E4;
  --color-secondary: #2DD4BF;
  --color-accent: #D97706;
  --color-accent-light: #FEF3C7;

  /* Surfaces */
  --color-bg: #F2F7F7;
  --color-surface: #FFFFFF;
  --color-surface-hover: #F8FAFA;

  /* Text */
  --color-text: #134E4A;
  --color-text-secondary: #5F7370;
  --color-text-muted: #94A3A0;
  --color-text-inverse: #FFFFFF;

  /* Semantic */
  --color-success: #10B981;
  --color-success-bg: #ECFDF5;
  --color-success-border: #6EE7B7;
  --color-error: #EF4444;
  --color-error-bg: #FEF2F2;
  --color-error-border: #FECACA;
  --color-warning: #F59E0B;
  --color-warning-bg: #FFFBEB;
  --color-destructive: #DC2626;

  /* Borders */
  --color-border: #D1E0DD;
  --color-border-light: #E2EDEA;

  /* Typography — CJK-capable stack */
  --font-heading: 'Inter', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
  --font-body: 'Inter', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Font sizes */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;

  /* Spacing (4pt grid) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 20px;
  --radius-full: 9999px;

  /* Shadows — Soft UI Evolution */
  --shadow-sm: 0 1px 2px rgba(13, 148, 136, 0.06);
  --shadow-md: 0 2px 8px rgba(13, 148, 136, 0.08), 0 1px 3px rgba(13, 148, 136, 0.06);
  --shadow-lg: 0 4px 16px rgba(13, 148, 136, 0.10), 0 2px 6px rgba(13, 148, 136, 0.06);
  --shadow-xl: 0 8px 32px rgba(13, 148, 136, 0.12), 0 4px 12px rgba(13, 148, 136, 0.08);

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
  --transition-slow: 300ms ease;

  /* Layout */
  --max-width: 800px;
  --header-height: 56px;
}

/* ===== Reset & Base ===== */
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 16px;
  -webkit-text-size-adjust: 100%;
}

body {
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--color-text);
  background: var(--color-bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ===== Focus styles ===== */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

/* ===== Scrollbar ===== */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-full);
}

/* ===== App Layout ===== */
.app {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 var(--space-4);
  min-height: 100vh;
  min-height: 100dvh;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: var(--header-height);
  margin-bottom: var(--space-8);
  border-bottom: 1px solid var(--color-border-light);
  position: sticky;
  top: 0;
  background: var(--color-bg);
  z-index: 50;
  backdrop-filter: blur(8px);
}

.app-header .logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-heading);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-primary-dark);
  text-decoration: none;
  letter-spacing: -0.02em;
  transition: color var(--transition-fast);
}

.app-header .logo:hover {
  color: var(--color-primary);
}

.logo-icon {
  width: 26px;
  height: 26px;
  color: var(--color-primary);
}

.app-header nav {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.app-header nav a {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.app-header nav a:hover {
  color: var(--color-primary-dark);
  background: var(--color-primary-bg);
}

.app-header nav a.nav-active {
  color: var(--color-primary);
  background: var(--color-primary-bg);
  font-weight: 600;
}

.app-main {
  padding-bottom: var(--space-12);
}

/* ===== Page Transitions ===== */
.page-enter-active,
.page-leave-active {
  transition: opacity var(--transition-base), transform var(--transition-base);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ===== Shared Components ===== */

/* Buttons */
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 10px 20px;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 44px;
  line-height: 1;
  text-decoration: none;
}

.btn-primary:hover {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-primary:active {
  transform: translateY(0);
  background: var(--color-primary-dark);
}

.btn-primary:disabled {
  background: var(--color-border);
  color: var(--color-text-muted);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 10px 20px;
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 44px;
  line-height: 1;
}

.btn-secondary:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-bg);
  color: var(--color-primary-dark);
}

.btn-secondary:active {
  background: var(--color-primary-border);
}

.btn-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  background: var(--color-surface);
  color: var(--color-destructive);
  border: 1px solid var(--color-error-border);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 44px;
  line-height: 1;
}

.btn-danger:hover {
  background: var(--color-error-bg);
  border-color: var(--color-error);
}

.btn-submit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 12px 28px;
  background: var(--color-accent);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 48px;
  line-height: 1;
}

.btn-submit:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.btn-submit:active {
  transform: translateY(0);
}

.btn-submit:disabled {
  background: var(--color-border);
  color: var(--color-text-muted);
  cursor: not-allowed;
  transform: none;
  filter: none;
  box-shadow: none;
}

/* Cards */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border-light);
  transition: box-shadow var(--transition-base), transform var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-md);
}

/* Status display */
.status-box {
  text-align: center;
  padding: var(--space-12) var(--space-6);
  color: var(--color-text-secondary);
}

/* Spinner */
.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border-light);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto var(--space-4);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Skeleton loading */
.skeleton {
  background: linear-gradient(90deg, var(--color-border-light) 25%, #E8F0EE 50%, var(--color-border-light) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-sm);
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Error text */
.error-text {
  color: var(--color-error);
  font-size: var(--text-sm);
  margin-top: var(--space-2);
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: var(--space-12) var(--space-6);
  color: var(--color-text-muted);
}

.empty-state svg {
  width: 48px;
  height: 48px;
  color: var(--color-border);
  margin-bottom: var(--space-4);
}

.empty-state p {
  font-size: var(--text-sm);
}

/* ===== Markdown Content (for v-html rendered elements) ===== */
.md-content p { margin-bottom: var(--space-2); }
.md-content strong { font-weight: 600; }
.md-content em { font-style: italic; }
.md-content code {
  background: var(--color-bg);
  padding: 1px 5px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.875em;
}
.md-content pre {
  background: var(--color-bg);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin-bottom: var(--space-2);
}
.md-content pre code {
  background: none;
  padding: 0;
}
.md-content ul, .md-content ol {
  padding-left: var(--space-6);
  margin-bottom: var(--space-2);
}
.md-content li { margin-bottom: var(--space-1); }
.md-content blockquote {
  border-left: 3px solid var(--color-primary-border);
  padding-left: var(--space-3);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}
.md-content h1, .md-content h2, .md-content h3, .md-content h4 {
  font-family: var(--font-heading);
  font-weight: 600;
  margin: var(--space-3) 0 var(--space-1);
}
.md-content h1 { font-size: var(--text-xl); }
.md-content h2 { font-size: var(--text-lg); }
.md-content h3 { font-size: var(--text-base); }
.md-content table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: var(--space-2);
}
.md-content th, .md-content td {
  border: 1px solid var(--color-border-light);
  padding: var(--space-1) var(--space-2);
  text-align: left;
}
.md-content th {
  background: var(--color-bg);
  font-weight: 600;
}

/* ===== Responsive ===== */
@media (min-width: 768px) {
  .app {
    padding: 0 var(--space-6);
  }
}
</style>
