<template>
  <Layout>
    <header class="header">
      <div class="header-left">
        <span class="breadcrumb">首页 / <span class="breadcrumb-current">数据源配置</span></span>
      </div>
    </header>

    <div class="page-content">
      <div class="page-header">
        <h1 class="page-title">数据源配置</h1>
        <button class="btn btn-primary" @click="showAddModal = true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          新增数据源
        </button>
      </div>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <select class="filter-select" v-model="filters.type" @change="fetchSources">
          <option value="">全部类型</option>
          <option value="news">新闻网站</option>
          <option value="rss">RSS订阅</option>
          <option value="wechat">微信公众号</option>
          <option value="social">社交媒体</option>
        </select>
        <select class="filter-select" v-model="filters.enabled" @change="fetchSources">
          <option value="">全部状态</option>
          <option value="true">运行中</option>
          <option value="false">已停止</option>
        </select>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
      </div>

      <!-- 数据源卡片网格 -->
      <div v-else class="source-grid">
        <div class="source-card" v-for="source in sources" :key="source.id">
          <div class="source-card-header">
            <div class="source-info">
              <div class="source-icon">{{ getSourceIcon(source.name) }}</div>
              <div>
                <div class="source-name">{{ source.name }}</div>
                <span class="source-type">{{ getTypeLabel(source.type) }}</span>
              </div>
            </div>
            <div class="source-status-badge" :class="{ online: source.enabled, offline: !source.enabled }">
              <span class="status-dot"></span>
              {{ source.enabled ? '运行中' : '已停止' }}
            </div>
          </div>
          <div class="source-card-body">
            <div class="source-meta">
              <div class="meta-item">
                <div class="meta-label">抓取间隔</div>
                <div class="meta-value">{{ source.crawl_interval || 30 }}分钟</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">今日抓取</div>
                <div class="meta-value">{{ source.today_count || 0 }}条</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">最后抓取</div>
                <div class="meta-value">{{ formatTime(source.last_crawl_at) }}</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">成功率</div>
                <div class="meta-value">{{ source.success_rate || 0 }}%</div>
              </div>
            </div>
          </div>
          <div class="source-card-footer">
            <div class="source-actions">
              <button class="action-btn" @click="editSource(source)">编辑</button>
              <button class="action-btn" @click="triggerCrawl(source.id)" :disabled="!source.enabled">手动抓取</button>
              <button class="action-btn danger" @click="deleteSource(source.id)">删除</button>
            </div>
            <div 
              class="toggle-switch" 
              :class="{ active: source.enabled }" 
              @click="toggleSource(source)"
            ></div>
          </div>
        </div>

        <!-- 新增数据源卡片 -->
        <div class="add-source-card" @click="showAddModal = true">
          <div class="add-icon">+</div>
          <span class="add-text">新增数据源</span>
        </div>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h2 class="modal-title">{{ editingSource ? '编辑数据源' : '新增数据源' }}</h2>
        
        <div class="form-group">
          <label class="form-label">名称</label>
          <input type="text" class="form-input" v-model="sourceForm.name" placeholder="数据源名称">
        </div>
        
        <div class="form-group">
          <label class="form-label">类型</label>
          <select class="form-select" v-model="sourceForm.type">
            <option value="news">新闻网站</option>
            <option value="rss">RSS订阅</option>
            <option value="wechat">微信公众号</option>
            <option value="social">社交媒体</option>
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">URL</label>
          <input type="text" class="form-input" v-model="sourceForm.url" placeholder="网站URL或RSS地址">
        </div>
        
        <div class="form-group">
          <label class="form-label">抓取间隔(分钟)</label>
          <input type="number" class="form-input" v-model.number="sourceForm.interval_minutes" placeholder="30">
        </div>
        
        <div class="modal-actions">
          <button class="btn btn-outline" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveSource">保存</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import { sourcesAPI } from '../api'

const loading = ref(true)
const sources = ref([])
const showAddModal = ref(false)
const editingSource = ref(null)

const filters = reactive({
  type: '',
  enabled: ''
})

const sourceForm = reactive({
  name: '',
  type: 'news',
  url: '',
  interval_minutes: 30,
  enabled: true
})

const typeLabels = {
  news: '新闻网站',
  rss: 'RSS订阅',
  wechat: '微信公众号',
  social: '社交媒体'
}

const getTypeLabel = (type) => typeLabels[type] || type

const getSourceIcon = (name) => {
  const icons = {
    '36kr': '🔷',
    '36氪': '🔷',
    '虎嗅': '🐯',
    '钛媒体': '⚡',
    '创业邦': '🚀',
    'RSS': '📡',
    '知乎': '💬'
  }
  return icons[name] || '📰'
}

const formatTime = (time) => {
  if (!time) return '从未'
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  return `${Math.floor(hours / 24)}天前`
}

const fetchSources = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.type) params.source_type = filters.type
    if (filters.enabled !== '') params.enabled = filters.enabled === 'true'
    
    const response = await sourcesAPI.getList(params)
    sources.value = response.data
  } catch (error) {
    console.error('获取数据源失败:', error)
  } finally {
    loading.value = false
  }
}

const editSource = (source) => {
  editingSource.value = source
  sourceForm.name = source.name
  sourceForm.type = source.type
  sourceForm.url = source.url || ''
  sourceForm.interval_minutes = source.crawl_interval || 30
  sourceForm.enabled = source.enabled
  showAddModal.value = true
}

const closeModal = () => {
  showAddModal.value = false
  editingSource.value = null
  sourceForm.name = ''
  sourceForm.type = 'news'
  sourceForm.url = ''
  sourceForm.interval_minutes = 30
  sourceForm.enabled = true
}

const saveSource = async () => {
  try {
    if (editingSource.value) {
      await sourcesAPI.update(editingSource.value.id, sourceForm)
    } else {
      await sourcesAPI.create(sourceForm)
    }
    closeModal()
    fetchSources()
  } catch (error) {
    alert('保存失败: ' + (error.response?.data?.detail || error.message))
  }
}

const toggleSource = async (source) => {
  try {
    await sourcesAPI.update(source.id, { enabled: !source.enabled })
    source.enabled = !source.enabled
  } catch (error) {
    alert('操作失败')
  }
}

const triggerCrawl = async (sourceId) => {
  try {
    await sourcesAPI.triggerCrawl(sourceId)
    alert('抓取任务已触发')
  } catch (error) {
    alert('触发失败: ' + (error.response?.data?.detail || error.message))
  }
}

const deleteSource = async (sourceId) => {
  if (!confirm('确定要删除这个数据源吗？')) return
  
  try {
    await sourcesAPI.delete(sourceId)
    fetchSources()
  } catch (error) {
    alert('删除失败')
  }
}

onMounted(() => {
  fetchSources()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--color-bg);
  border-radius: 8px;
  padding: 24px;
  width: 100%;
  max-width: 480px;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.add-source-card {
  background: var(--color-bg-alt);
  border: 2px dashed var(--color-border);
  border-radius: 8px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  cursor: pointer;
  transition: all 0.2s;
}

.add-source-card:hover {
  border-color: var(--color-primary);
  background: var(--color-hover);
}

.add-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-bg);
  border: 2px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--color-secondary);
  margin-bottom: 12px;
}

.add-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-secondary);
}
</style>
