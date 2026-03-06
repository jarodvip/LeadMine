<template>
  <Layout>
    <header class="header">
      <div class="header-left">
        <span class="breadcrumb">首页 / <span class="breadcrumb-current">用户管理</span></span>
      </div>
      <div class="header-right">
        <button class="btn btn-primary" @click="showCreateDialog = true">新增用户</button>
      </div>
    </header>

    <div class="page-content">
      <h1 class="page-title">用户管理</h1>

      <div class="toolbar">
        <div class="search-box">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" placeholder="搜索用户名/邮箱..." v-model="searchKeyword" @keyup.enter="fetchUsers">
        </div>
        <select class="form-select" v-model="filterRole" @change="fetchUsers">
          <option value="">全部角色</option>
          <option value="admin">管理员</option>
          <option value="user">普通用户</option>
          <option value="viewer">查看者</option>
        </select>
        <select class="form-select" v-model="filterStatus" @change="fetchUsers">
          <option value="">全部状态</option>
          <option value="true">启用</option>
          <option value="false">禁用</option>
        </select>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
      </div>

      <template v-else>
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>邮箱</th>
              <th>角色</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.id }}</td>
              <td>{{ user.username }}</td>
              <td>{{ user.email || '-' }}</td>
              <td>
                <span class="role-tag" :class="user.role">{{ getRoleLabel(user.role) }}</span>
              </td>
              <td>
                <span class="status-tag" :class="user.is_active ? 'active' : 'inactive'">
                  {{ user.is_active ? '启用' : '禁用' }}
                </span>
              </td>
              <td>{{ formatDate(user.created_at) }}</td>
              <td>
                <button class="btn-link" @click="handleEdit(user)">编辑</button>
                <button class="btn-link" @click="handleResetPassword(user)">重置密码</button>
                <button class="btn-link danger" @click="handleDelete(user)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="pagination">
          <button class="btn btn-outline btn-sm" :disabled="page <= 1" @click="page--; fetchUsers()">
            上一页
          </button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <button class="btn btn-outline btn-sm" :disabled="page >= totalPages" @click="page++; fetchUsers()">
            下一页
          </button>
        </div>
      </template>
    </div>

    <div v-if="showCreateDialog" class="modal-overlay" @click.self="showCreateDialog = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingUser ? '编辑用户' : '新增用户' }}</h3>
          <button class="modal-close" @click="showCreateDialog = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">用户名 *</label>
            <input type="text" class="form-input" v-model="userForm.username" :disabled="!!editingUser">
          </div>
          <div class="form-group" v-if="!editingUser">
            <label class="form-label">密码 *</label>
            <input type="password" class="form-input" v-model="userForm.password">
          </div>
          <div class="form-group">
            <label class="form-label">邮箱</label>
            <input type="email" class="form-input" v-model="userForm.email">
          </div>
          <div class="form-group">
            <label class="form-label">角色</label>
            <select class="form-select" v-model="userForm.role">
              <option value="viewer">查看者</option>
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showCreateDialog = false">取消</button>
          <button class="btn btn-primary" @click="handleSave">保存</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import { usersAPI } from '../api'

const loading = ref(false)
const users = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterRole = ref('')
const filterStatus = ref('')

const showCreateDialog = ref(false)
const editingUser = ref(null)

const userForm = reactive({
  username: '',
  password: '',
  email: '',
  role: 'user'
})

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const roleLabels = {
  admin: '管理员',
  user: '普通用户',
  viewer: '查看者'
}

const getRoleLabel = (role) => roleLabels[role] || role

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value || undefined,
      role: filterRole.value || undefined,
      is_active: filterStatus.value ? filterStatus.value === 'true' : undefined
    }
    const res = await usersAPI.getList(params)
    users.value = res.data.data
    total.value = res.data.total
  } catch (error) {
    console.error('获取用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleEdit = (user) => {
  editingUser.value = user
  userForm.username = user.username
  userForm.email = user.email || ''
  userForm.password = ''
  userForm.role = user.role
  showCreateDialog.value = true
}

const handleSave = async () => {
  try {
    if (editingUser.value) {
      await usersAPI.update(editingUser.value.id, {
        email: userForm.email,
        role: userForm.role
      })
      alert('更新成功')
    } else {
      await usersAPI.create(userForm)
      alert('创建成功')
    }
    showCreateDialog.value = false
    editingUser.value = null
    resetForm()
    fetchUsers()
  } catch (error) {
    alert(error.response?.data?.detail || '操作失败')
  }
}

const handleResetPassword = async (user) => {
  if (!confirm(`确定重置用户 ${user.username} 的密码吗？`)) return
  try {
    const res = await usersAPI.resetPassword(user.id)
    alert(`密码已重置，新密码: ${res.data.new_password}`)
  } catch (error) {
    alert('重置密码失败')
  }
}

const handleDelete = async (user) => {
  if (!confirm(`确定删除用户 ${user.username} 吗？此操作不可恢复。`)) return
  try {
    await usersAPI.delete(user.id)
    alert('删除成功')
    fetchUsers()
  } catch (error) {
    alert(error.response?.data?.detail || '删除失败')
  }
}

const resetForm = () => {
  userForm.username = ''
  userForm.password = ''
  userForm.email = ''
  userForm.role = 'user'
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.toolbar .search-box {
  flex: 1;
  max-width: 300px;
}

.role-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.role-tag.admin {
  background: #fef0f0;
  color: #f56c6c;
}

.role-tag.user {
  background: #f0f9ff;
  color: #409eff;
}

.role-tag.viewer {
  background: #f4f4f5;
  color: #909399;
}

.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.active {
  background: #f0f9f0;
  color: #67c23a;
}

.status-tag.inactive {
  background: #f4f4f5;
  color: #909399;
}

.btn-link {
  background: none;
  border: none;
  color: #409eff;
  cursor: pointer;
  padding: 4px 8px;
  font-size: 13px;
}

.btn-link:hover {
  text-decoration: underline;
}

.btn-link.danger {
  color: #f56c6c;
}

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

.modal {
  background: white;
  border-radius: 8px;
  width: 100%;
  max-width: 480px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #eee;
}
</style>
