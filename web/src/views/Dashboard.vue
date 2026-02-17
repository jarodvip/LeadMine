<template>
  <Layout>
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-left">
        <span class="breadcrumb">首页 / <span class="breadcrumb-current">仪表盘</span></span>
      </div>
      <div class="header-right">
        <div class="search-box">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" placeholder="搜索线索..." v-model="searchKeyword" @keyup.enter="handleSearch">
        </div>
        <svg class="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
      </div>
    </header>

    <!-- 页面内容 -->
    <div class="page-content">
      <h1 class="page-title">仪表盘</h1>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
      </div>
      
      <template v-else>
        <!-- 统计卡片 -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">今日新增线索</div>
            <div class="stat-value">{{ stats.today_leads || 0 }}</div>
            <div class="stat-change positive">数据持续更新中</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">本周新增线索</div>
            <div class="stat-value">{{ stats.week_leads || 0 }}</div>
            <div class="stat-change positive">数据持续更新中</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">本月新增线索</div>
            <div class="stat-value">{{ stats.month_leads || 0 }}</div>
            <div class="stat-change positive">数据持续更新中</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">线索总数</div>
            <div class="stat-value">{{ stats.total_leads || 0 }}</div>
            <div class="stat-change">数据持续更新中</div>
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="content-grid">
          <!-- 线索类型分布 -->
          <div class="content-card">
            <div class="card-header">
              <span class="card-title">线索类型分布</span>
              <router-link to="/leads" class="card-action">查看详情 →</router-link>
            </div>
            <div class="card-body">
              <div class="chart-area">
                <div class="chart-placeholder"></div>
                <div class="chart-legend">
                  <div class="legend-item" v-for="type in leadTypes" :key="type.value">
                    <span class="legend-label">
                      <span class="legend-dot" :style="{ background: type.color }"></span>
                      {{ type.label }}
                    </span>
                    <span class="legend-value">{{ stats.leads_by_type?.[type.value] || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 最近线索 -->
          <div class="content-card">
            <div class="card-header">
              <span class="card-title">最近线索</span>
              <router-link to="/leads" class="card-action">查看全部 →</router-link>
            </div>
            <div class="card-body">
              <ul class="lead-list">
                <li class="lead-item" v-for="lead in stats.recent_leads" :key="lead.id">
                  <div class="lead-info">
                    <div class="lead-company">{{ lead.company_name }}</div>
                    <div class="lead-meta">{{ lead.source_name }} · {{ formatTime(lead.created_at) }}</div>
                  </div>
                  <span class="type-tag" :class="lead.event_type">{{ getTypeLabel(lead.event_type) }}</span>
                </li>
                <li v-if="!stats.recent_leads?.length" class="lead-item">
                  <div class="lead-info" style="text-align: center; width: 100%; color: var(--color-secondary);">
                    暂无线索数据
                  </div>
                </li>
              </ul>
            </div>
          </div>

        </div>

        <!-- 数据源状态 -->
        <div class="content-card">
          <div class="card-header">
            <span class="card-title">数据源状态</span>
            <router-link to="/sources" class="card-action">管理数据源 →</router-link>
          </div>
          <div class="card-body">
            <ul class="source-list">
              <li class="source-item" v-for="source in sources" :key="source.id">
                <div class="source-info">
                  <div class="source-icon">{{ getSourceIcon(source.name) }}</div>
                  <div>
                    <div class="source-name">{{ source.name }}</div>
                    <div class="source-status">
                      <span class="source-status-dot" :class="{ online: source.enabled, offline: !source.enabled }"></span>
                      {{ source.enabled ? '运行中' : '已停止' }}
                    </div>
                  </div>
                </div>
                <button class="btn btn-sm btn-outline" @click="triggerCrawl(source.id)" :disabled="!source.enabled">
                  手动抓取
                </button>
              </li>
              <li v-if="!sources.length" class="source-item">
                <div class="source-info" style="text-align: center; width: 100%; color: var(--color-secondary);">
                  暂无数据源
                </div>
              </li>
            </ul>
          </div>
        </div>
      </template>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import { leadsAPI, sourcesAPI } from '../api'

const router = useRouter()

const loading = ref(true)
const searchKeyword = ref('')
const stats = ref({})
const sources = ref([])

const leadTypes = [
  { value: 'financing', label: '融资事件', color: 'var(--color-financing)' },
  { value: 'acquisition', label: '并购收购', color: 'var(--color-acquisition)' },
  { value: 'product', label: '产品发布', color: 'var(--color-product)' },
  { value: 'expansion', label: '扩产扩张', color: 'var(--color-expansion)' },
  { value: 'procurement', label: '招标采购', color: 'var(--color-procurement)' },
  { value: 'executive', label: '高管动态', color: 'var(--color-executive)' },
  { value: 'policy', label: '政策利好', color: 'var(--color-policy)' }
]

const getTypeLabel = (type) => {
  const found = leadTypes.find(t => t.value === type)
  return found ? found.label : type
}

const getSourceIcon = (name) => {
  const icons = {
    '36kr': '🔷',
    '36氪': '🔷',
    '虎嗅': '🐯',
    '钛媒体': '⚡',
    'RSS': '📡',
    '知乎': '💬'
  }
  return icons[name] || '📰'
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  const hours = Math.floor(diff / 3600000)
  
  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  return `${Math.floor(hours / 24)}天前`
}

const handleSearch = () => {
  if (searchKeyword.value) {
    router.push({ path: '/leads', query: { keyword: searchKeyword.value } })
  }
}

const fetchDashboard = async () => {
  try {
    const [statsRes, sourcesRes] = await Promise.all([
      leadsAPI.getDashboard(),
      sourcesAPI.getList()
    ])
    stats.value = statsRes.data
    sources.value = sourcesRes.data
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
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

onMounted(() => {
  fetchDashboard()
})
</script>
