<template>
  <div class="login-wrapper">
    <div class="login-container">
      <div class="login-card">
        <div class="logo">
          <div class="logo-icon-lg">
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
          <div class="logo-text-lg">LEADMINE</div>
        </div>
        
        <h1 class="login-title">登录到您的账户</h1>
        
        <div v-if="errorMsg" class="message error">{{ errorMsg }}</div>
        
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label class="form-label" for="username">用户名</label>
            <input 
              type="text" 
              id="username" 
              class="form-input" 
              placeholder="请输入用户名"
              v-model="username"
              required
            >
          </div>
          
          <div class="form-group">
            <label class="form-label" for="password">密码</label>
            <input 
              type="password" 
              id="password" 
              class="form-input" 
              placeholder="请输入密码"
              v-model="password"
              required
            >
          </div>
          
          <div class="form-options">
            <label class="checkbox-label">
              <input type="checkbox" v-model="rememberMe">
              记住我
            </label>
            <a href="#" class="forgot-link">忘记密码？</a>
          </div>
          
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
        
        <div class="login-footer">
          © 2026 LeadMine. All rights reserved.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../api'

const router = useRouter()

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const loading = ref(false)
const errorMsg = ref('')

const handleLogin = async () => {
  loading.value = true
  errorMsg.value = ''
  
  try {
    const response = await authAPI.login({
      username: username.value,
      password: password.value
    })
    
    localStorage.setItem('token', response.data.access_token)
    
    // 获取用户信息
    const userRes = await authAPI.getCurrentUser()
    localStorage.setItem('user', JSON.stringify(userRes.data))
    
    router.push('/')
  } catch (error) {
    errorMsg.value = error.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-alt);
}
</style>
