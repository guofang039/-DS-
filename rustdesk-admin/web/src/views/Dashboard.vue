<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="用户总数" :value="stats.users" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="设备总数" :value="stats.devices" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="在线设备" :value="stats.online" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="今日连接" :value="stats.connections" />
        </el-card>
      </el-col>
    </el-row>
    
    <el-card style="margin-top: 20px">
      <template #header>
        <span>服务器配置</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="hbbs 服务">{{ config.hbbs }}</el-descriptions-item>
        <el-descriptions-item label="hbbr 服务">{{ config.hbbr }}</el-descriptions-item>
        <el-descriptions-item label="API 服务">{{ config.api_server }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const stats = ref({ users: 0, devices: 0, online: 0, connections: 0 })
const config = ref({})

onMounted(async () => {
  try {
    const [users, devices, serverConfig] = await Promise.all([
      api.get('/users').catch(() => []),
      api.get('/devices').catch(() => []),
      api.get('/server-config').catch(() => ({}))
    ])
    stats.value.users = users.length || 0
    stats.value.devices = devices.length || 0
    stats.value.online = devices.filter(d => d.is_online).length || 0
    config.value = serverConfig
  } catch (err) {
    console.error(err)
  }
})
</script>
