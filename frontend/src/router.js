import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('./views/Dashboard.vue')
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('./views/Chat.vue')
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('./views/Documents.vue')
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('./views/History.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('./views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router