<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header mb-12">
      <h1 class="text-3xl font-bold" style="color: #00d4ff; text-shadow: 0 0 15px rgba(0, 212, 255, 0.6);">
        智能控制台
      </h1>
      <p class="text-gray-400 mt-2">系统概览与快速操作</p>
    </div>

    <!-- 统计卡片 -->
    <div class="flex justify-between gap-6" style="display: flex; justify-content: space-between; gap: 24px; margin-bottom: 3rem;">
      <StatsCard
        title="文档总数"
        :value="stats.documents"
        :icon="Document"
        color="blue"
        :trend="+12"
      />
      <StatsCard
        title="对话会话"
        :value="stats.sessions"
        :icon="ChatDotRound"
        color="purple"
        :trend="+5"
      />
      <StatsCard
        title="查询次数"
        :value="stats.queries"
        :icon="Search"
        color="green"
        :trend="+23"
      />
      <StatsCard
        title="API调用"
        :value="stats.apiCalls"
        :icon="Connection"
        color="yellow"
        :trend="+18"
      />
    </div>

    <!-- 主要功能区 -->
    <div class="space-y-10 mb-12">
      <!-- 快速对话 -->
      <div class="tech-card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-tech-text-primary">快速对话</h2>
        </div>
        <div class="card-body">
          <div class="quick-chat">
            <el-input
              v-model="quickMessage"
              type="textarea"
              :rows="3"
              placeholder="输入您的问题，快速获得答案..."
              class="mb-4"
            />
            <el-button
              type="primary"
              @click="sendQuickMessage"
              :loading="isLoading"
              class="tech-button"
            >
              <el-icon class="mr-2"><Promotion /></el-icon>
              发送消息
            </el-button>
          </div>

          <div v-if="quickResponse" class="quick-response mt-6">
            <div class="response-header mb-2 text-tech-text-secondary text-sm">
              AI 回复：
            </div>
            <div class="response-content">
              {{ quickResponse }}
            </div>
          </div>
        </div>
      </div>

      <!-- 快捷操作 -->
      <div class="tech-card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-tech-text-primary">快捷操作</h2>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-4 gap-4">
            <QuickAction
              :icon="Upload"
              label="上传文档"
              @click="navigateTo('/documents')"
            />
            <QuickAction
              :icon="ChatDotRound"
              label="开始对话"
              @click="navigateTo('/chat')"
            />
            <QuickAction
              :icon="Setting"
              label="系统配置"
              @click="navigateTo('/settings')"
            />
            <QuickAction
              :icon="Clock"
              label="历史记录"
              @click="navigateTo('/history')"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 活动图表 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
      <!-- 使用趋势 -->
      <div class="tech-card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-tech-text-primary">使用趋势</h2>
        </div>
        <div class="card-body">
          <ActivityChart :data="activityData" />
        </div>
      </div>

      <!-- 最近文档 -->
      <div class="tech-card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-tech-text-primary">最近文档</h2>
        </div>
        <div class="card-body">
          <div class="recent-docs">
            <div
              v-for="doc in recentDocs"
              :key="doc.id"
              class="doc-item"
            >
              <el-icon class="doc-icon"><Document /></el-icon>
              <div class="doc-info">
                <div class="doc-name">{{ doc.name }}</div>
                <div class="doc-time">{{ doc.time }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Document,
  ChatDotRound,
  Search,
  Connection,
  Upload,
  Setting,
  Clock,
  Promotion
} from '@element-plus/icons-vue'
import StatsCard from '../components/dashboard/StatsCard.vue'
import QuickAction from '../components/dashboard/QuickAction.vue'
import ActivityChart from '../components/dashboard/ActivityChart.vue'

const router = useRouter()

// 统计数据
const stats = ref({
  documents: 156,
  sessions: 42,
  queries: 1280,
  apiCalls: 3567
})

// 快速对话
const quickMessage = ref('')
const quickResponse = ref('')
const isLoading = ref(false)

// 最近文档
const recentDocs = ref([
  { id: 1, name: 'project_docs.pdf', time: '10分钟前' },
  { id: 2, name: 'api_reference.txt', time: '2小时前' },
  { id: 3, name: 'user_manual.pdf', time: '昨天' },
  { id: 4, name: 'tech_spec.pdf', time: '2天前' },
])

// 活动数据
const activityData = ref([
  { date: '周一', value: 120 },
  { date: '周二', value: 150 },
  { date: '周三', value: 180 },
  { date: '周四', value: 160 },
  { date: '周五', value: 200 },
  { date: '周六', value: 90 },
  { date: '周日', value: 110 },
])

// 发送快速消息
const sendQuickMessage = async () => {
  if (!quickMessage.value.trim()) {
    ElMessage.warning('请输入消息内容')
    return
  }

  isLoading.value = true
  quickResponse.value = ''

  // 模拟API调用
  setTimeout(() => {
    quickResponse.value = '这是一个快速响应示例。您可以通过点击"开始对话"按钮进入完整的对话界面，获得更好的交互体验。'
    isLoading.value = false
    ElMessage.success('获得响应')
  }, 1500)
}

// 导航
const navigateTo = (path) => {
  router.push(path)
}

onMounted(() => {
  // 可以加载真实数据
})
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  height: calc(100vh - 64px - 48px); // 减去header高度和padding
  overflow-y: auto;
  overflow-x: auto; // 允许横向滚动以防内容溢出

  // 自定义滚动条
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

.tech-card {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);

  &:hover {
    box-shadow: var(--tech-shadow-glow);
    border-color: var(--tech-border-hover);
  }

  .card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--tech-glass-border);
    background: rgba(255, 255, 255, 0.02);
  }

  .card-body {
    padding: 20px;
  }
}

.tech-button {
  background: linear-gradient(135deg, var(--tech-neon-blue) 0%, var(--tech-neon-purple) 100%);
  border: none;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
  }
}

.quick-response {
  padding: 16px;
  background: rgba(0, 212, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;

  .response-content {
    color: var(--tech-text-primary);
    line-height: 1.6;
  }
}

.recent-docs {
  .doc-item {
    display: flex;
    align-items: center;
    padding: 12px;
    margin-bottom: 8px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--tech-glass-border);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      background: rgba(0, 212, 255, 0.05);
      border-color: var(--tech-border-hover);
      transform: translateX(4px);
    }

    .doc-icon {
      font-size: 24px;
      color: var(--tech-neon-blue);
      margin-right: 12px;
    }

    .doc-info {
      .doc-name {
        color: var(--tech-text-primary);
        font-size: 14px;
        margin-bottom: 4px;
      }

      .doc-time {
        color: var(--tech-text-muted);
        font-size: 12px;
      }
    }
  }
}
</style>