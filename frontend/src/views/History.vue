<template>
  <div class="history">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>查询历史</span>
          <el-button @click="refreshHistory" :loading="loading">
            刷新
          </el-button>
        </div>
      </template>
      
      <div v-if="queryHistory.length === 0" class="empty-state">
        <el-empty description="暂无查询历史" />
      </div>
      
      <el-timeline v-else>
        <el-timeline-item
          v-for="item in queryHistory"
          :key="item.id"
          :timestamp="item.created_at"
          placement="top"
        >
          <el-card class="history-item">
            <template #header>
              <div class="history-header">
                <strong>问题:</strong> {{ item.query }}
              </div>
            </template>
            
            <div class="history-content">
              <h4>回答:</h4>
              <p>{{ item.response }}</p>
              
              <div v-if="item.sources && item.sources.length > 0">
                <h4>相关文档:</h4>
                <ul>
                  <li v-for="(source, index) in item.sources" :key="index">
                    {{ source.filename }} (相似度: {{ (source.similarity * 100).toFixed(2) }}%)
                  </li>
                </ul>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRagStore } from '../store/ragStore'
import { ElMessage } from 'element-plus'

const store = useRagStore()
const loading = computed(() => store.loading)
const queryHistory = computed(() => store.queryHistory)

const refreshHistory = async () => {
  try {
    await store.fetchQueryHistory()
    ElMessage.success('历史记录已刷新')
  } catch (error) {
    ElMessage.error('刷新失败: ' + error.message)
  }
}

onMounted(() => {
  store.fetchQueryHistory()
})
</script>

<style scoped>
.history {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

.history-item {
  margin-bottom: 10px;
}

.history-header {
  font-weight: bold;
  color: #409EFF;
}

.history-content {
  margin-top: 10px;
}

.history-content h4 {
  color: #606266;
  margin-bottom: 8px;
}

.history-content p {
  line-height: 1.6;
  margin-bottom: 15px;
}

.history-content ul {
  padding-left: 20px;
}

.history-content li {
  margin-bottom: 5px;
  color: #909399;
}
</style>