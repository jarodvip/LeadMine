<template>
  <Layout>
    <header class="header">
      <div class="header-left">
        <span class="breadcrumb">首页 / <span class="breadcrumb-current">线索管理</span></span>
      </div>
      <div class="header-right">
        <div class="search-box">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" placeholder="搜索线索..." v-model="filters.keyword" @keyup.enter="fetchLeads">
        </div>
      </div>
    </header>

    <div class="page-content">
      <div class="page-header">
        <h1 class="page-title">线索管理</h1>
        <button class="btn btn-outline" @click="exportLeads">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          导出
        </button>
      </div>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <select class="filter-select" v-model="filters.status" @change="fetchLeads">
          <option value="">全部状态</option>
          <option value="new">新增</option>
          <option value="contacted">已联系</option>
          <option value="converted">已转化</option>
          <option value="invalid">无效</option>
        </select>
        <select class="filter-select" v-model="filters.event_type" @change="fetchLeads">
          <option value="">全部类型</option>
          <option value="financing">融资事件</option>
          <option value="acquisition">并购收购</option>
          <option value="product">产品发布</option>
          <option value="expansion">扩产扩张</option>
          <option value="procurement">招标采购</option>
          <option value="executive">高管动态</option>
          <option value="policy">政策利好</option>
        </select>
        <input type="date" class="filter-date" v-model="filters.start_date" @change="fetchLeads">
        <span style="color: var(--color-secondary);">至</span>
        <input type="date" class="filter-date" v-model="filters.end_date" @change="fetchLeads">
        <button class="btn btn-outline btn-sm" @click="resetFilters">重置</button>
      </div>

      <div v-if="selectedCount > 0" class="filter-bar">
        <span style="color: var(--color-primary); font-weight: 600;">已选择 {{ selectedCount }} 条线索</span>
        <button class="btn btn-outline btn-sm" @click="handleBatchUpdateStatus">批量更新状态</button>
        <button class="btn btn-outline btn-sm" @click="handleBatchAssign">批量分配</button>
        <button class="btn btn-outline btn-sm" @click="handleBatchDelete">批量删除</button>
        <button class="btn btn-outline btn-sm" @click="clearSelection">取消选择</button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
      </div>

      <!-- 表格 -->
      <div v-else class="table-card">
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    :checked="allVisibleSelected"
                    :indeterminate.prop="someVisibleSelected && !allVisibleSelected"
                    @change="toggleSelectAll($event)"
                  >
                </th>
                <th>序号</th>
                <th>企业名称</th>
                <th>事件类型</th>
                <th>事件详情</th>
                <th>来源</th>
                <th>等级</th>
                <th>评分</th>
                <th>置信度</th>
                <th>状态</th>
                <th>发布时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(lead, index) in leads" :key="lead.id">
                <td>
                  <input
                    type="checkbox"
                    :checked="selectedLeadIds.includes(lead.id)"
                    @change="toggleLeadSelection(lead.id, $event.target.checked)"
                  >
                </td>
                <td>{{ (pagination.page - 1) * pagination.page_size + index + 1 }}</td>
                <td class="company-name">{{ lead.company_name }}</td>
                <td><span class="type-tag" :class="lead.event_type">{{ getTypeLabel(lead.event_type) }}</span></td>
                <td class="event-detail">{{ lead.event_detail || '-' }}</td>
                <td class="source-name">{{ lead.source_name || '-' }}</td>
                <td><span class="grade-tag" :class="getGradeClass(lead.grade)">{{ lead.grade || '-' }}</span></td>
                <td>{{ lead.score ?? 0 }}</td>
                <td>
                  <div class="confidence-bar">
                    <div class="confidence-track">
                      <div class="confidence-fill" :class="getConfidenceClass(lead.confidence)" :style="{ width: lead.confidence + '%' }"></div>
                    </div>
                    <span class="confidence-value">{{ lead.confidence }}</span>
                  </div>
                </td>
                <td><span class="status-tag" :class="lead.status">{{ getStatusLabel(lead.status) }}</span></td>
                <td>{{ formatDate(lead.published_at) }}</td>
                <td>
                  <div class="action-btns">
                    <router-link :to="`/leads/${lead.id}`" class="action-btn">查看</router-link>
                    <button class="action-btn" @click="deleteLead(lead.id)">删除</button>
                  </div>
                </td>
              </tr>
              <tr v-if="!leads.length">
                <td colspan="12" style="text-align: center; padding: 40px; color: var(--color-secondary);">
                  暂无数据
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div class="pagination" v-if="pagination.total > 0">
          <div class="pagination-info">
            共 <strong>{{ pagination.total }}</strong> 条记录，第 <strong>{{ pagination.page }}</strong>/<strong>{{ Math.ceil(pagination.total / pagination.page_size) }}</strong> 页
          </div>
          <div class="pagination-btns">
            <button class="page-btn" :disabled="pagination.page <= 1" @click="changePage(pagination.page - 1)">上一页</button>
            <button
              v-for="p in visiblePages"
              :key="p"
              class="page-btn"
              :class="{ active: p === pagination.page }"
              @click="changePage(p)"
            >
              {{ p }}
            </button>
            <button class="page-btn" :disabled="pagination.page >= Math.ceil(pagination.total / pagination.page_size)" @click="changePage(pagination.page + 1)">下一页</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import Layout from '../components/Layout.vue'
import { leadsAPI } from '../api'

const route = useRoute()

const loading = ref(true)
const leads = ref([])
const selectedLeadIds = ref([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })

const filters = reactive({
  status: '',
  event_type: '',
  keyword: '',
  start_date: '',
  end_date: ''
})

const leadTypes = {
  financing: '融资',
  acquisition: '并购',
  product: '产品',
  expansion: '扩产',
  procurement: '招标',
  executive: '高管',
  policy: '政策'
}

const statusLabels = {
  new: '新增',
  contacted: '已联系',
  converted: '已转化',
  invalid: '无效'
}

const selectedCount = computed(() => selectedLeadIds.value.length)
const visibleLeadIds = computed(() => leads.value.map(lead => lead.id))
const visibleLeadIdSet = computed(() => new Set(visibleLeadIds.value))
const allVisibleSelected = computed(() => visibleLeadIds.value.length > 0 && visibleLeadIds.value.every(id => selectedLeadIds.value.includes(id)))
const someVisibleSelected = computed(() => visibleLeadIds.value.some(id => selectedLeadIds.value.includes(id)))

const getTypeLabel = (type) => leadTypes[type] || type
const getStatusLabel = (status) => statusLabels[status] || status

const getGradeClass = (grade) => {
  if (grade === 'A') return 'grade-a'
  if (grade === 'B') return 'grade-b'
  if (grade === 'C') return 'grade-c'
  return 'grade-d'
}

const getConfidenceClass = (confidence) => {
  if (confidence >= 70) return 'high'
  if (confidence >= 40) return 'medium'
  return 'low'
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

const visiblePages = computed(() => {
  const total = Math.ceil(pagination.value.total / pagination.value.page_size)
  const current = pagination.value.page
  const pages = []

  let start = Math.max(1, current - 2)
  let end = Math.min(total, current + 2)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const clearSelection = () => {
  selectedLeadIds.value = []
}

const toggleLeadSelection = (leadId, checked) => {
  if (checked) {
    if (!selectedLeadIds.value.includes(leadId)) {
      selectedLeadIds.value = [...selectedLeadIds.value, leadId]
    }
    return
  }

  selectedLeadIds.value = selectedLeadIds.value.filter(id => id !== leadId)
}

const toggleSelectAll = (event) => {
  if (event.target.checked) {
    selectedLeadIds.value = [...visibleLeadIds.value]
    return
  }

  clearSelection()
}

const fetchLeads = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.page_size
    }

    if (filters.status) params.status = filters.status
    if (filters.event_type) params.event_type = filters.event_type
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.start_date) params.start_date = filters.start_date
    if (filters.end_date) params.end_date = filters.end_date

    const response = await leadsAPI.getList(params)
    leads.value = response.data.data
    selectedLeadIds.value = selectedLeadIds.value.filter(id => visibleLeadIdSet.value.has(id))
    pagination.value = {
      page: response.data.page,
      page_size: response.data.page_size,
      total: response.data.total
    }
  } catch (error) {
    console.error('获取线索失败:', error)
  } finally {
    loading.value = false
  }
}

const changePage = (page) => {
  pagination.value.page = page
  fetchLeads()
}

const resetFilters = () => {
  filters.status = ''
  filters.event_type = ''
  filters.keyword = ''
  filters.start_date = ''
  filters.end_date = ''
  pagination.value.page = 1
  clearSelection()
  fetchLeads()
}

const exportLeads = async () => {
  try {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.event_type) params.event_type = filters.event_type
    if (filters.keyword) params.keyword = filters.keyword

    const response = await leadsAPI.exportLeads(params)
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `leads_${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
  } catch (error) {
    alert('导出失败')
  }
}

const handleBatchUpdateStatus = async () => {
  const status = window.prompt('请输入新状态：new、contacted、converted、invalid')
  if (!status) return

  try {
    await leadsAPI.batchUpdateStatus(selectedLeadIds.value, status)
    await fetchLeads()
    clearSelection()
  } catch (error) {
    alert('批量更新状态失败')
  }
}

const handleBatchAssign = async () => {
  const assignedTo = window.prompt('请输入分配对象')
  if (!assignedTo) return

  try {
    await leadsAPI.batchAssign(selectedLeadIds.value, assignedTo)
    await fetchLeads()
    clearSelection()
  } catch (error) {
    alert('批量分配失败')
  }
}

const handleBatchDelete = async () => {
  if (!window.confirm(`确定要删除选中的 ${selectedCount.value} 条线索吗？`)) return

  try {
    await leadsAPI.batchDelete(selectedLeadIds.value)
    await fetchLeads()
    clearSelection()
  } catch (error) {
    alert('批量删除失败')
  }
}

const deleteLead = async (id) => {
  if (!confirm('确定要删除这条线索吗？')) return

  try {
    await leadsAPI.delete(id)
    fetchLeads()
  } catch (error) {
    alert('删除失败')
  }
}

watch(() => route.query.keyword, (newKeyword) => {
  filters.keyword = newKeyword || ''
  pagination.value.page = 1
  clearSelection()
  fetchLeads()
})

onMounted(() => {
  fetchLeads()
})
</script>
