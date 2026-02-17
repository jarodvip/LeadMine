import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import Leads from '../views/Leads.vue'
import LeadDetail from '../views/LeadDetail.vue'
import Articles from '../views/Articles.vue'
import Sources from '../views/Sources.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/leads',
    name: 'Leads',
    component: Leads,
    meta: { requiresAuth: true }
  },
  {
    path: '/leads/:id',
    name: 'LeadDetail',
    component: LeadDetail,
    meta: { requiresAuth: true }
  },
  {
    path: '/articles',
    name: 'Articles',
    component: Articles,
    meta: { requiresAuth: true }
  },
  {
    path: '/sources',
    name: 'Sources',
    component: Sources,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
