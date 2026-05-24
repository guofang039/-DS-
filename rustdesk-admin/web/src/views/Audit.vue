<template>
  <div>
    <el-card>
      <template #header>
        <span>审计日志</span>
      </template>
      <el-table :data="logs" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="user_id" label="用户ID" width="100" />
        <el-table-column prop="action" label="操作" width="150">
          <template #default="{ row }">
            <el-tag>{{ actionLabel(row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_peer" label="目标设备" width="120" />
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ row.created_at ? new Date(row.created_at).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="details" label="详情" />
      </el-table>
      
      <el-pagination
        style="margin-top: 20px; justify-content: flex-end"
        :current-page="page"
        :page-size="100"
        layout="prev, pager, next"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const logs = ref([])
const loading = ref(false)
const page = ref(1)

const actionLabel = (action) => {
  const labels = {
    login: '登录',
    logout: '登出',
    device_register: '设备注册',
    connect: '连接',
    disconnect: '断开',
    file_transfer: '文件传输'
  }
  return labels[action] || action
}

const loadLogs = async () => {
  loading.value = true
  try {
    logs.value = await api.get('/audit/logs', {
      params: { offset: (page.value - 1) * 100, limit: 100 }
    })
  } catch (err) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (p) => {
  page.value = p
  loadLogs()
}

onMounted(loadLogs)
</script>
