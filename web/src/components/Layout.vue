<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="28" cy="28" r="8" fill="#1A1A1A"/>
              <circle cx="10" cy="10" r="5" fill="#1A1A1A"/>
              <circle cx="46" cy="10" r="4" fill="#666666"/>
              <circle cx="8" cy="40" r="4" fill="#666666"/>
              <circle cx="48" cy="42" r="5" fill="#1A1A1A"/>
              <line x1="15" y1="13" x2="23" y2="23" stroke="#1A1A1A" stroke-width="1.5"/>
              <line x1="38" y1="13" x2="32" y2="22" stroke="#666666" stroke-width="1.5"/>
              <line x1="12" y1="37" x2="23" y2="31" stroke="#666666" stroke-width="1.5"/>
              <line x1="42" y1="39" x2="33" y2="32" stroke="#1A1A1A" stroke-width="1.5"/>
              <line x1="13" y1="14" x2="11" y2="37" stroke="#E5E5E5" stroke-width="1"/>
              <line x1="43" y1="12" x2="46" y2="39" stroke="#E5E5E5" stroke-width="1"/>
            </svg>
          </div>
          <span class="logo-text">LEADMINE</span>
        </div>
      </div>
      
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" :class="{ active: route.path === '/' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
          </svg>
          <span>仪表盘</span>
        </router-link>
        <router-link to="/leads" class="nav-item" :class="{ active: route.path.startsWith('/leads') }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          <span>线索管理</span>
        </router-link>
        <router-link to="/articles" class="nav-item" :class="{ active: route.path === '/articles' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
          <span>文章列表</span>
        </router-link>
        <router-link to="/sources" class="nav-item" :class="{ active: route.path === '/sources' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          <span>数据源配置</span>
        </router-link>
      </nav>
      
      <div class="sidebar-footer">
        <div class="user-info" @click="handleLogout">
          <div class="user-avatar">{{ userInitial }}</div>
          <div>
            <div class="user-name">{{ userName }}</div>
            <div class="user-role">管理员</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const userName = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user).username : 'Admin'
})

const userInitial = computed(() => {
  return userName.value.charAt(0).toUpperCase()
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>
