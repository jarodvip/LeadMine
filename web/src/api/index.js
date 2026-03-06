import axios from 'axios'

// API 请求地址 - 本地开发使用 localhost，部署时改为服务器地址
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加 Token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 认证 API
export const authAPI = {
  login: (data) => api.post('/auth/login', 
    new URLSearchParams({
      username: data.username,
      password: data.password
    }).toString(),
    {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }
  ),
  register: (data) => api.post('/auth/register', data),
  getCurrentUser: () => api.get('/auth/me')
}

// 线索管理 API
export const leadsAPI = {
  getList: (params) => api.get('/leads', { params }),
  getDetail: (id) => api.get(`/leads/${id}`),
  create: (data) => api.post('/leads', data),
  update: (id, data) => api.patch(`/leads/${id}`, data),
  delete: (id) => api.delete(`/leads/${id}`),
  getDashboard: () => api.get('/leads/stats/dashboard'),
  exportLeads: (params) => api.get('/leads/export', { params }),
  batchUpdateStatus: (leadIds, status) => api.post('/leads/batch/update-status', { lead_ids: leadIds, status }),
  batchAssign: (leadIds, assignedTo) => api.post('/leads/batch/assign', { lead_ids: leadIds, assigned_to: assignedTo }),
  batchDelete: (leadIds) => api.post('/leads/batch/delete', { lead_ids: leadIds })
}

// 文章 API
export const articlesAPI = {
  getList: (params) => api.get('/articles', { params }),
  getDetail: (id) => api.get(`/articles/${id}`)
}

// 数据源 API
export const sourcesAPI = {
  getList: (params) => api.get('/sources', { params }),
  getDetail: (id) => api.get(`/sources/${id}`),
  create: (data) => api.post('/sources', data),
  update: (id, data) => api.patch(`/sources/${id}`, data),
  delete: (id) => api.delete(`/sources/${id}`),
  triggerCrawl: (id) => api.post(`/sources/${id}/crawl`)
}

// 用户管理 API
export const usersAPI = {
  getList: (params) => api.get('/users', { params }),
  getDetail: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.patch(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
  resetPassword: (id) => api.post(`/users/${id}/reset-password`)
}

// 数据处理 API
export const processorAPI = {
  enrichLead: (leadId) => api.post(`/processor/leads/${leadId}/enrich`),
  processArticle: (articleId) => api.post(`/processor/articles/${articleId}/process`),
  processPending: (limit) => api.post(`/processor/articles/process?limit=${limit}`)
}

export default api
