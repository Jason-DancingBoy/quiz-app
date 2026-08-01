import { createRouter, createWebHashHistory } from 'vue-router'
import DocumentList from './views/DocumentList.vue'
import QuizPage from './views/QuizPage.vue'
import ReviewPage from './views/ReviewPage.vue'
import HistoryPage from './views/HistoryPage.vue'

const routes = [
  { path: '/', component: DocumentList },
  { path: '/quiz/:id', component: QuizPage, props: true },
  { path: '/quiz/:id/review', component: ReviewPage, props: true },
  { path: '/history', component: HistoryPage },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
