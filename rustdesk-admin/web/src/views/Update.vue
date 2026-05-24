<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统更新</span>
          <el-button type="primary" @click="checkUpdate" :loading="checking">
            检查更新
          </el-button>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="当前版本">{{ currentVersion }}</el-descriptions-item>
        <el-descriptions-item label="最新版本">
          <el-tag v-if="updateInfo.has_update" type="success">{{ updateInfo.latest_version }}</el-tag>
          <span v-else>{{ updateInfo.latest_version }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="更新状态">
          <el-tag v-if="updateInfo.has_update" type="warning">有新版本</el-tag>
          <el-tag v-else type="success">已是最新</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="下载地址">
          <el-link v-if="updateInfo.download_url" :href="updateInfo.download_url" target="_blank" type="primary">
            点击下载
          </el-link>
          <span v-else>-</span>
        </el-descriptions-item>
      </el-descriptions>
      
      <div v-if="updateInfo.changelog" style="margin-top: 20px">
        <h4>更新日志</h4>
        <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px">{{ updateInfo.changelog }}</pre>
      </div>
    </el-card>
    
    <el-card style="margin-top: 20px">
      <template #header>
        <span>历史版本</span>
      </template>
      <el-table :data="releases" v-loading="loadingReleases">
        <el-table-column prop="version" label="版本" width="100" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="created_at" label="发布时间" width="180">
          <template #default="{ row }">
            {{ row.created_at ? new Date(row.created_at).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="下载" width="200">
          <template #default="{ row }">
            <el-select v-model="row.selectedAsset" placeholder="选择平台" size="small" style="width: 120px">
              <el-option
                v-for="asset in row.assets"
                :key="asset.name"
                :label="asset.name"
                :value="asset.download_url"
              />
            </el-select>
            <el-button
              v-if="row.selectedAsset"
              size="small"
              type="primary"
              @click="downloadRelease(row.selectedAsset)"
              style="margin-left: 5px"
            >
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const currentVersion = ref('1.4.6')
const checking = ref(false)
const loadingReleases = ref(false)
const releases = ref([])

const updateInfo = reactive({
  has_update: false,
  current_version: '1.4.6',
  latest_version: '1.4.6',
  download_url: null,
  changelog: ''
})

const checkUpdate = async () => {
  checking.value = true
  try {
    const res = await api.get('/update/check')
    Object.assign(updateInfo, res)
    if (res.has_update) {
      ElMessage.success(`发现新版本 ${res.latest_version}`)
    } else {
      ElMessage.info('已是最新版本')
    }
  } catch (err) {
    ElMessage.error('检查更新失败')
  } finally {
    checking.value = false
  }
}

const loadReleases = async () => {
  loadingReleases.value = true
  try {
    releases.value = await api.get('/update/releases')
    releases.value.forEach(r => {
      r.selectedAsset = r.assets?.[0]?.download_url || ''
    })
  } catch (err) {
    ElMessage.error('加载版本列表失败')
  } finally {
    loadingReleases.value = false
  }
}

const downloadRelease = (url) => {
  window.open(url, '_blank')
}

onMounted(() => {
  checkUpdate()
  loadReleases()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
