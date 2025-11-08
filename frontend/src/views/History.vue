<template>
  <div class="history-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="text-2xl font-bold" style="color: #00d4ff; text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);">
        历史记录
      </h1>
      <el-button @click="refreshHistory" :loading="loading" class="refresh-btn">
        <el-icon class="mr-1"><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 二级菜单 -->
    <div class="tab-header">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="Chat 历史记录" name="chat" />
        <el-tab-pane label="RAG 查询记录" name="query" />
      </el-tabs>
    </div>

    <!-- 历史记录列表 -->
    <div class="history-content">
      <!-- Chat 历史记录 -->
      <div v-if="activeTab === 'chat'">
        <div v-if="chatHistory.length === 0" class="empty-state">
          <el-empty description="暂无Chat历史记录" />
        </div>

        <el-timeline v-else>
          <el-timeline-item
            v-for="item in chatHistory"
            :key="item.id"
            :timestamp="formatDate(item.timestamp)"
            placement="top"
          >
            <el-card class="history-item">
              <template #header>
                <div class="history-header">
                  <el-icon class="header-icon"><ChatDotRound /></el-icon>
                  <span class="query-text">{{ item.query }}</span>
                </div>
              </template>

              <div class="history-content">
                <div class="history-meta">
                  <el-tag size="small" type="info">
                    <el-icon><Clock /></el-icon>
                    {{ item.title || 'Chat会话' }}
                  </el-tag>
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>

      <!-- RAG 查询记录 -->
      <div v-else>
        <div v-if="queryHistory.length === 0" class="empty-state">
          <el-empty description="暂无RAG查询记录" />
        </div>

        <el-timeline v-else>
          <el-timeline-item
            v-for="item in queryHistory"
            :key="item.id"
            :timestamp="formatDate(item.created_at)"
            placement="top"
          >
            <el-card class="history-item">
              <template #header>
                <div class="history-header">
                  <el-icon class="header-icon"><Search /></el-icon>
                  <span class="query-text">{{ item.query }}</span>
                </div>
              </template>

              <div class="history-body">
                <div class="response-preview" v-if="item.response">
                  {{ item.response.length > 150 ? item.response.substring(0, 150) + '...' : item.response }}
                </div>
                <div class="history-meta">
                  <el-tag size="small" type="success">
                    <el-icon><Document /></el-icon>
                    RAG查询
                  </el-tag>
                  <el-tag size="small" type="info" v-if="item.sources && item.sources.length > 0">
                    <el-icon><Link /></el-icon>
                    {{ item.sources.length }} 个源文档
                  </el-tag>
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRagStore } from '../store/ragStore'
import { ElMessage } from 'element-plus'
import { Refresh, ChatDotRound, Clock, Search, Document, Link } from '@element-plus/icons-vue'

const store = useRagStore()

const loading = computed(() => store.loading)
const queryHistory = computed(() => store.queryHistory)
const chatHistory = computed(() => store.chatHistory)
const pagination = computed(() => store.pagination)
const activeTab = ref(store.activeHistoryTab)

const currentPage = ref(1)
const pageSize = ref(20)
const total = computed(() => pagination.value.total)

const loadHistory = async (tab = activeTab.value, page = 1, size = pageSize.value) => {
  try {
    if (tab === 'chat') {
      await store.fetchChatHistory(page, size)
    } else {
      await store.fetchQueryHistory(page, size)
    }
  } catch (error) {
    ElMessage.error('加载历史记录失败: ' + error.message)
  }
}

const refreshHistory = async () => {
  try {
    await loadHistory()
    ElMessage.success('历史记录已刷新')
  } catch (error) {
    ElMessage.error('刷新失败: ' + error.message)
  }
}

const handleTabChange = async (tab) => {
  store.activeHistoryTab = tab
  currentPage.value = 1
  await loadHistory(tab, 1, pageSize.value)
}

const handleSizeChange = async (size) => {
  pageSize.value = size
  currentPage.value = 1
  await loadHistory(activeTab.value, 1, size)
}

const handleCurrentChange = async (page) => {
  currentPage.value = page
  await loadHistory(activeTab.value, page, pageSize.value)
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.history-container {
  height: calc(100vh - 64px - 50px);
  display: flex;
  flex-direction: column;
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-shrink: 0;
}

.tab-header {
  margin-bottom: 20px;
  flex-shrink: 0;
}

/* Element Plus 标签页自定义样式 */
:deep(.el-tabs__header) {
  margin: 0;
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 8px;
  padding: 0 16px;
  backdrop-filter: blur(10px);
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.el-tabs__item) {
  color: var(--tech-text-muted);
  font-weight: 500;
  border-bottom: 2px solid transparent;
}

:deep(.el-tabs__item:hover) {
  color: var(--tech-neon-blue);
}

:deep(.el-tabs__item.is-active) {
  color: var(--tech-neon-blue);
  border-bottom-color: var(--tech-neon-blue);
}

.refresh-btn {
  background: linear-gradient(135deg, var(--tech-neon-blue) 0%, var(--tech-neon-purple) 100%);
  border: none;
  color: white;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

.history-content {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;

  /* 自定义滚动条 */
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(0, 212, 255, 0.3);
    border-radius: 4px;

    &:hover {
      background: rgba(0, 212, 255, 0.5);
    }
  }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.history-item {
  margin-bottom: 16px;
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.history-item:hover {
  box-shadow: var(--tech-shadow-glow);
  border-color: var(--tech-border-hover);
}

.history-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--tech-text-primary);
}

.header-icon {
  color: var(--tech-neon-blue);
  font-size: 18px;
}

.query-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-meta {
  margin-top: 8px;
}

.history-content {
  margin-top: 8px;
}

.history-body {
  margin-top: 8px;
}

.response-preview {
  color: var(--tech-text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  border-left: 3px solid var(--tech-neon-blue);
}

.pagination-wrapper {
  flex-shrink: 0;
  margin-top: 20px;
  padding: 16px 0;
  display: flex;
  justify-content: center;
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

/* Element Plus 分页组件自定义样式 */
:deep(.el-pagination) {
  --el-pagination-text-color: var(--tech-text-primary);
  --el-pagination-bg-color: transparent;
  --el-pagination-button-color: var(--tech-text-primary);
  --el-pagination-button-bg-color: transparent;
  --el-pagination-button-disabled-bg-color: rgba(255, 255, 255, 0.1);
}

:deep(.el-pagination .el-pager li) {
  background: transparent;
  color: var(--tech-text-primary);
  border: 1px solid var(--tech-glass-border);
  margin: 0 4px;
  border-radius: 4px;
}

:deep(.el-pagination .el-pager li:hover) {
  color: var(--tech-neon-blue);
  border-color: var(--tech-neon-blue);
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--tech-neon-blue);
  border-color: var(--tech-neon-blue);
  color: white;
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  background: transparent;
  color: var(--tech-text-primary);
  border: 1px solid var(--tech-glass-border);
  border-radius: 4px;
}

:deep(.el-pagination .btn-prev:hover),
:deep(.el-pagination .btn-next:hover) {
  color: var(--tech-neon-blue);
  border-color: var(--tech-neon-blue);
}

:deep(.el-pagination .el-select .el-input__wrapper) {
  background: transparent;
  border: 1px solid var(--tech-glass-border);
}
</style>