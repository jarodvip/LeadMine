<template>
  <Layout>
    <header class="header">
      <div class="header-left">
        <span class="breadcrumb">首页 / <span class="breadcrumb-current">文章列表</span></span>
      </div>
      <div class="header-right">
        <div class="search-box">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" placeholder="搜索文章..." v-model="filters.keyword" @keyup.enter="fetchArticles">
        </div>
      </div>
    </header>

    <div class="page-content">
      <div class="page-header">
        <h1 class="page-title">文章列表</h1>
      </div>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <select class="filter-select" v-model="filters.source_name" @change="fetchArticles">
          <option value="">全部来源</option>
          <option value="36kr">36氪</option>
          <option value="huxiu">虎嗅</option>
          <option value="rss">RSS订阅</option>
        </select>
        <input type="date" class="filter-date" v-model="filters.start_date" @change="fetchArticles">
        <span style="color: var(--color-secondary);">至</span>
        <input type="date" class="filter-date" v-model="filters.end_date" @change="fetchArticles">
        <button class="btn btn-outline btn-sm" @click="resetFilters">重置</button>
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
                <th>序号</th>
                <th>标题</th>
                <th>来源</th>
                <th>分类</th>
                <th>爬取时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(article, index) in articles" :key="article.id">
                <td>{{ (pagination.page - 1) * pagination.page_size + index + 1 }}</td>
                <td class="company-name">{{ article.title }}</td>
                <td class="source-name">{{ article.source_name }}</td>
                <td class="source-name">{{ article.category || '-' }}</td>
                <td>{{ formatDateTime(article.crawled_at) }}</td>
                <td>
                  <div class="action-btns">
                    <a :href="article.url" target="_blank" class="action-btn">查看原文</a>
                  </div>
                </td>
              </tr>
              <tr v-if="!articles.length">
                <td colspan="6" style="text-align: center; padding: 40px; color: var(--color-secondary);">
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
            <button class="page-btn" :disabled="pagination.page >= Math.ceil(pagination.total / pagination.page_size)" @click="changePage(pagination.page + 1)">下一页</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import { articlesAPI } from '../api'

const loading = ref(true)
const articles = ref([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })

const filters = reactive({
  source_name: '',
  keyword: '',
  start_date: '',
  end_date: ''
})

const formatDateTime = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const fetchArticles = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.page_size
    }
    
    if (filters.source_name) params.source_name = filters.source_name
    if (filters.keyword) params.keyword = filters.keyword
    
    const response = await articlesAPI.getList(params)
    articles.value = response.data.data
    pagination.value = {
      page: response.data.page,
      page_size: response.data.page_size,
      total: response.data.total
    }
  } catch (error) {
    console.error('获取文章失败:', error)
  } finally {
    loading.value = false
  }
}

const changePage = (page) => {
  pagination.value.page = page
  fetchArticles()
}

const resetFilters = () => {
  filters.source_name = ''
  filters.keyword = ''
  filters.start_date = ''
  filters.end_date = ''
  pagination.value.page = 1
  fetchArticles()
}

onMounted(() => {
  fetchArticles()
})
</script>
