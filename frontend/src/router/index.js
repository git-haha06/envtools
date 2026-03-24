import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'dashboard', component: () => import('../views/Dashboard.vue') },
        { path: 'environments', name: 'environments', component: () => import('../views/Environments.vue') },
        { path: 'install', name: 'install', component: () => import('../views/Install.vue') },
        { path: 'env-vars', name: 'envVars', component: () => import('../views/EnvVars.vue') },
        { path: 'settings', name: 'settings', component: () => import('../views/Settings.vue') },
      ],
    },
  ],
})

export default router
