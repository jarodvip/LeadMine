<template>
  <Layout>
    <header class="header">
      <div class="header-left">
        <span class="breadcrumb">首页 / 线索管理 / <span class="breadcrumb-current">线索详情</span></span>
      </div>
      <div class="header-right">
        <router-link to="/leads" class="btn btn-outline btn-sm">返回列表</router-link>
      </div>
    </header>

    <div class="page-content">
      <div class="page-header">
        <h1 class="page-title">线索详情</h1>
        <div style="display: flex; gap: 12px;">
          <button class="btn btn-outline" @click="exportLead">导出线索</button>
          <button class="btn btn-primary" @click="saveLead">保存修改</button>
        </div>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
      </div>

      <template v-else-if="lead">
        <div class="detail-grid">
          <!-- 左侧详情 -->
          <div class="detail-card">
            <div class="detail-header">
              <div class="company-info">
                <h1>{{ lead.company_name }}</h1>
                <span class="type-tag" :class="lead.event_type">{{ getTypeLabel(lead.event_type) }}</span>
              </div>
            </div>
            <div class="detail-body">
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">事件详情</div>
                  <div class="info-value">{{ lead.event_detail || '-' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">涉及金额</div>
                  <div class="info-value">{{ lead.event_amount || '-' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">数据来源</div>
                  <div class="info-value">{{ lead.source_name || '-' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">发布时间</div>
                  <div class="info-value">{{ formatDateTime(lead.published_at) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">创建时间</div>
                  <div class="info-value">{{ formatDateTime(lead.created_at) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">线索ID</div>
                  <div class="info-value">#{{ lead.id }}</div>
                </div>
              </div>

              <div class="confidence-section">
                <div class="info-label">置信度</div>
                <div class="confidence-bar">
                  <div class="confidence-track">
                    <div class="confidence-fill" :style="{ width: lead.confidence + '%' }"></div>
                  </div>
                  <span class="confidence-value">{{ lead.confidence }}</span>
                </div>
              </div>

              <div class="score-section">
                <div class="score-grid">
                  <div class="score-item">
                    <div class="info-label">线索等级</div>
                    <span class="grade-tag" :class="getGradeClass(lead.grade)">{{ lead.grade || '-' }}</span>
                  </div>
                  <div class="score-item">
                    <div class="info-label">匹配评分</div>
                    <div class="score-value">{{ lead.score ?? 0 }}</div>
                  </div>
                </div>
                <div class="follow-up-box" v-if="lead.follow_up_hint">
                  <div class="info-label">跟进建议</div>
                  <div class="follow-up-value">{{ lead.follow_up_hint }}</div>
                </div>
              </div>

              <div class="enrichment-section">
                <div class="section-header">
                  <span class="info-label">企业信息</span>
                  <button class="btn btn-outline btn-sm" @click="handleEnrich" :disabled="enriching">
                    {{ enriching ? '补充中...' : '补充企业信息' }}
                  </button>
                </div>
                <div v-if="lead.enrichment_data" class="enrichment-grid">
                  <div class="enrich-item" v-if="lead.enrichment_data.legal_person">
                    <span class="enrich-label">法人</span>
                    <span class="enrich-value">{{ lead.enrichment_data.legal_person }}</span>
                  </div>
                  <div class="enrich-item" v-if="lead.enrichment_data.registered_capital">
                    <span class="enrich-label">注册资本</span>
                    <span class="enrich-value">{{ lead.enrichment_data.registered_capital }}</span>
                  </div>
                  <div class="enrich-item" v-if="lead.enrichment_data.establishment_date">
                    <span class="enrich-label">成立日期</span>
                    <span class="enrich-value">{{ lead.enrichment_data.establishment_date }}</span>
                  </div>
                  <div class="enrich-item" v-if="lead.enrichment_data.business_status">
                    <span class="enrich-label">经营状态</span>
                    <span class="enrich-value">{{ lead.enrichment_data.business_status }}</span>
                  </div>
                  <div class="enrich-item" v-if="lead.enrichment_data.phone">
                    <span class="enrich-label">电话</span>
                    <span class="enrich-value">{{ lead.enrichment_data.phone }}</span>
                  </div>
                  <div class="enrich-item" v-if="lead.enrichment_data.email">
                    <span class="enrich-label">邮箱</span>
                    <span class="enrich-value">{{ lead.enrichment_data.email }}</span>
                  </div>
                  <div class="enrich-item full" v-if="lead.enrichment_data.address">
                    <span class="enrich-label">地址</span>
                    <span class="enrich-value">{{ lead.enrichment_data.address }}</span>
                  </div>
                  <div class="enrich-item full" v-if="lead.enrichment_data.business_scope">
                    <span class="enrich-label">经营范围</span>
                    <span class="enrich-value">{{ lead.enrichment_data.business_scope }}</span>
                  </div>
                </div>
                <div v-else class="enrichment-empty">
                  点击"补充企业信息"获取企业工商数据
                </div>
              </div>

              <div class="status-section">
                <div class="info-grid">
                  <div class="form-group">
                    <label class="form-label">线索状态</label>
                    <select class="form-select" v-model="leadData.status">
                      <option value="new">新增</option>
                      <option value="contacted">已联系</option>
                      <option value="converted">已转化</option>
                      <option value="invalid">无效</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label class="form-label">分配给</label>
                    <input type="text" class="form-input" v-model="leadData.assigned_to" placeholder="输入销售人员">
                  </div>
                </div>
                <div class="form-group">
                  <label class="form-label">销售备注</label>
                  <textarea class="form-textarea" v-model="leadData.notes" placeholder="添加跟进备注..."></textarea>
                </div>
                <div class="action-bar">
                  <button class="btn btn-primary btn-sm" @click="updateStatus">更新状态</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧来源文章 -->
          <div class="detail-card source-card" v-if="article">
            <div class="source-header">
              <span class="source-title">来源文章</span>
            </div>
            <div class="source-body">
              <div class="source-meta">
                <div>{{ article.source_name }} · {{ formatDateTime(article.crawled_at) }}</div>
              </div>
              <h3 style="font-size: 16px; margin-bottom: 12px;">
                {{ article.title }}
              </h3>
              <div class="source-summary">{{ article.content?.slice(0, 500) }}...</div>
              <a :href="article.source_url" target="_blank" class="source-link">
                查看原文 →
              </a>
            </div>
          </div>
        </div>
      </template>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import { leadsAPI, articlesAPI, processorAPI } from '../api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const lead = ref(null)
const article = ref(null)
const enriching = ref(false)

const leadData = reactive({
  status: 'new',
  assigned_to: '',
  notes: ''
})

const leadTypes = {
  financing: '融资事件',
  acquisition: '并购收购',
  product: '产品发布',
  expansion: '扩产扩张',
  procurement: '招标采购',
  executive: '高管动态',
  policy: '政策利好'
}

const getTypeLabel = (type) => leadTypes[type] || type

const getGradeClass = (grade) => {
  if (grade === 'A') return 'grade-a'
  if (grade === 'B') return 'grade-b'
  if (grade === 'C') return 'grade-c'
  return 'grade-d'
}

const formatDateTime = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const fetchLead = async () => {
  loading.value = true
  try {
    const leadId = route.params.id
    const [leadRes] = await Promise.all([
      leadsAPI.getDetail(leadId)
    ])
    
    lead.value = leadRes.data
    leadData.status = leadRes.data.status
    leadData.assigned_to = leadRes.data.assigned_to || ''
    leadData.notes = leadRes.data.sales_notes || ''
    
    // 获取来源文章
    if (leadRes.data.source_article_id) {
      try {
        const articleRes = await articlesAPI.getDetail(leadRes.data.source_article_id)
        article.value = articleRes.data
      } catch (e) {
        console.log('文章不存在')
      }
    }
  } catch (error) {
    console.error('获取线索失败:', error)
    alert('线索不存在')
    router.push('/leads')
  } finally {
    loading.value = false
  }
}

const saveLead = async () => {
  try {
    await leadsAPI.update(lead.value.id, {
      status: leadData.status,
      assigned_to: leadData.assigned_to,
      sales_notes: leadData.notes
    })
    alert('保存成功')
  } catch (error) {
    alert('保存失败')
  }
}

const updateStatus = async () => {
  await saveLead()
}

const handleEnrich = async () => {
  if (!lead.value.company_name || lead.value.company_name === '未知') {
    alert('企业名称无效')
    return
  }
  enriching.value = true
  try {
    const res = await processorAPI.enrichLead(lead.value.id)
    if (res.data.data) {
      lead.value.enrichment_data = res.data.data
    }
    lead.value.score = res.data.score
    lead.value.grade = res.data.grade
    lead.value.follow_up_hint = res.data.follow_up_hint
    alert('企业信息补充成功')
  } catch (error) {
    alert('企业信息补充失败')
  } finally {
    enriching.value = false
  }
}

const exportLead = () => {
  // 导出单条线索
  const data = [
    ['企业名称', lead.value.company_name],
    ['事件类型', getTypeLabel(lead.value.event_type)],
    ['事件详情', lead.value.event_detail],
    ['涉及金额', lead.value.event_amount],
    ['数据来源', lead.value.source_name],
    ['发布时间', formatDateTime(lead.value.published_at)],
    ['置信度', lead.value.confidence],
    ['线索等级', lead.value.grade || ''],
    ['匹配评分', lead.value.score ?? 0],
    ['跟进建议', lead.value.follow_up_hint || ''],
    ['状态', leadData.status],
    ['分配给', leadData.assigned_to],
    ['备注', leadData.notes]
  ]
  
  let csv = '\uFEFF' // BOM for UTF-8
  data.forEach(row => {
    csv += row.map(cell => `"${cell || ''}"`).join(',') + '\n'
  })
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `lead_${lead.value.id}_${lead.value.company_name}.csv`
  link.click()
}

onMounted(() => {
  fetchLead()
})
</script>

<style scoped>
.enrichment-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.enrichment-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.enrich-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.enrich-item.full {
  grid-column: 1 / -1;
}

.enrich-label {
  font-size: 12px;
  color: #999;
}

.enrich-value {
  font-size: 14px;
  color: #333;
}

.enrichment-empty {
  padding: 20px;
  text-align: center;
  color: #999;
  background: #f9f9f9;
  border-radius: 6px;
}
</style>
