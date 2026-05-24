<template>
  <div>
    <el-card>
      <template #header>
        <span>设备管理</span>
      </template>
      <el-table :data="devices" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="peer_id" label="设备ID" width="120" />
        <el-table-column prop="hostname" label="主机名" />
        <el-table-column prop="platform" label="平台" width="100" />
        <el-table-column prop="group_name" label="分组" width="100" />
        <el-table-column prop="ip" label="IP地址" width="140" />
        <el-table-column prop="is_online" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_online ? 'success' : 'info'">
              {{ row.is_online ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_seen" label="最后在线" width="180">
          <template #default="{ row }">
            {{ row.last_seen ? new Date(row.last_seen).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="deleteDevice(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const devices = ref([])
const loading = ref(false)

const loadDevices = async () => {
  loading.value = true
  try {
    devices.value = await api.get('/devices')
  } catch (err) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const deleteDevice = async (row) => {
  await ElMessageBox.confirm('确定删除该设备？', '提示', { type: 'warning' })
  try {
    await api.delete(`/devices/${row.id}`)
    ElMessage.success('删除成功')
    loadDevices()
  } catch (err) {
    ElMessage.error(err.detail || '删除失败')
  }
}

onMounted(loadDevices)
</script>
