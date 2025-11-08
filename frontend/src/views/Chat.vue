<template>
  <div class="chat-container">
    <!-- 会话列表侧边栏 -->
    <div class="chat-sidebar">
      <ChatSidebar
        :sessions="sessions"
        :activeSessionId="activeSessionId"
        @select="selectSession"
        @create="createNewSession"
        @delete="deleteSession"
      />
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-main">
      <!-- 聊天标题栏 -->
      <div class="chat-header">
        <div class="header-content">
          <h2 class="chat-title">
            {{ currentSession?.title || '新对话' }}
          </h2>
          <div class="header-controls">
            <!-- 模型选择 -->
            <el-select
              v-model="selectedModel"
              size="small"
              class="model-select"
              placeholder="选择模型"
              :loading="loadingModels"
            >
              <el-option-group
                v-for="(models, provider) in groupedModelOptions"
                :key="provider"
                :label="provider"
              >
                <el-option
                  v-for="model in models"
                  :key="model.value"
                  :label="model.label"
                  :value="model.value"
                />
              </el-option-group>
            </el-select>
            <!-- RAG开关 -->
            <el-switch
              v-model="useRAG"
              active-text="RAG"
              inactive-text="普通"
              size="small"
            />
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <ChatWindow
        :messages="currentMessages"
        :loading="isLoading"
        ref="chatWindow"
        class="chat-messages"
      />

      <!-- 输入区域 -->
      <div class="chat-input-wrapper">
        <InputBar
          v-model="inputMessage"
          :disabled="isLoading"
          @send="sendMessage"
          @stop="stopGeneration"
          :is-generating="isGenerating"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import ChatWindow from '../components/chat/ChatWindow.vue'
import InputBar from '../components/chat/InputBar.vue'
import { useChatStore } from '../store/chatStore'
import llmService from '../services/llmService'

const chatStore = useChatStore()

// 状态
const sessions = computed(() => chatStore.sessions)
const activeSessionId = computed(() => chatStore.activeSessionId)
const currentSession = computed(() => chatStore.currentSession)
const currentMessages = computed(() => chatStore.currentMessages)
const isLoading = ref(false)
const isGenerating = ref(false)
const inputMessage = ref('')
const selectedModel = ref('gpt-3.5-turbo')
const useRAG = ref(true)

// 模型相关状态
const availableModels = ref([])
const loadingModels = ref(false)
const groupedModelOptions = ref({})

// Refs
const chatWindow = ref(null)

// 方法
const selectSession = async (sessionId) => {
  await chatStore.selectSession(sessionId)
}

const createNewSession = async () => {
  const session = await chatStore.createSession()
  if (session) {
    ElMessage.success('新会话已创建')
  }
}

const deleteSession = async (sessionId) => {
  await chatStore.deleteSession(sessionId)
  ElMessage.success('会话已删除')
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入消息内容')
    return
  }

  const message = inputMessage.value
  inputMessage.value = ''
  isLoading.value = true
  isGenerating.value = true

  try {
    await chatStore.sendMessage({
      message,
      model: selectedModel.value,
      useRAG: useRAG.value,
      stream: true
    })

    // 滚动到底部
    await nextTick()
    chatWindow.value?.scrollToBottom()
  } catch (error) {
    ElMessage.error('发送消息失败：' + error.message)
  } finally {
    isLoading.value = false
    isGenerating.value = false
  }
}

const stopGeneration = () => {
  chatStore.stopGeneration()
  isGenerating.value = false
}

// 加载可用模型
const loadAvailableModels = async () => {
  try {
    loadingModels.value = true
    const models = await llmService.getAllModels()
    console.log('【调试】原始模型数据:', models)

    // 只保留聊天模型
    const chatModels = llmService.getChatModels(models)
    console.log('【调试】过滤后的聊天模型:', chatModels)
    availableModels.value = chatModels

    // 按提供商分组
    const grouped = llmService.getGroupedModelOptions(chatModels)
    console.log('【调试】分组的模型选项:', grouped)
    groupedModelOptions.value = grouped

    // 如果当前选择的模型不在列表中，选择第一个
    const hasCurrentModel = chatModels.some(m => m.name === selectedModel.value)
    if (!hasCurrentModel && chatModels.length > 0) {
      selectedModel.value = chatModels[0].name
    }

    console.log('✓ 已加载模型:', chatModels.length, '个')
    console.log('✓ 分组结果:', Object.keys(grouped).join(', '))
  } catch (error) {
    console.error('✗ 加载模型失败:', error)
    ElMessage.error('加载模型列表失败')
  } finally {
    loadingModels.value = false
  }
}

// 生命周期
onMounted(async () => {
  await chatStore.loadSessions()
  await loadAvailableModels()
})
</script>

<style lang="scss" scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 64px);
  background: transparent;
  gap: 1px;
  padding: 0;
}

.chat-sidebar {
  width: 320px;
  flex-shrink: 0;
  background: var(--tech-glass-bg);
  border-right: 1px solid var(--tech-glass-border);
  backdrop-filter: blur(10px);
  position: relative;

  &::after {
    content: '';
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 1px;
    background: linear-gradient(
      180deg,
      transparent,
      var(--tech-neon-blue) 30%,
      var(--tech-neon-blue) 70%,
      transparent
    );
    opacity: 0.3;
  }
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: transparent;
  overflow: hidden;
}

.chat-header {
  padding: 20px 24px;
  background: var(--tech-glass-bg);
  border-bottom: 1px solid var(--tech-glass-border);
  backdrop-filter: blur(10px);
  position: relative;

  &::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 1px;
    background: linear-gradient(
      90deg,
      transparent,
      var(--tech-neon-blue) 50%,
      transparent
    );
    opacity: 0.4;
  }

  .header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .chat-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--tech-text-primary);
    background: linear-gradient(135deg, var(--tech-neon-blue), var(--tech-neon-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .header-controls {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.chat-messages {
  flex: 1;
  overflow: auto;
}

.chat-input-wrapper {
  padding: 20px 24px;
  padding-bottom: 60px; // 增加底部内边距，避免与状态栏贴在一起
  background: var(--tech-glass-bg);
  border-top: 1px solid var(--tech-glass-border);
  backdrop-filter: blur(10px);
  position: relative;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    height: 1px;
    background: linear-gradient(
      90deg,
      transparent,
      var(--tech-neon-purple) 50%,
      transparent
    );
    opacity: 0.4;
  }
}

// Element Plus 组件样式覆盖
:deep(.model-select) {
  width: 128px;

  .el-input__wrapper {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--tech-glass-border);
    box-shadow: none;
    transition: all 0.3s ease;

    &:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: var(--tech-border-hover);
    }

    &.is-focus {
      background: rgba(255, 255, 255, 0.08);
      border-color: var(--tech-neon-blue);
      box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.2);
    }
  }

  .el-input__inner {
    color: var(--tech-text-primary);
  }
}

:deep(.el-switch) {
  &.is-checked .el-switch__core {
    background: var(--tech-neon-blue);
    border-color: var(--tech-neon-blue);
    box-shadow: 0 0 8px rgba(0, 212, 255, 0.4);
  }

  .el-switch__core {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid var(--tech-glass-border);
  }

  .el-switch__action {
    background: #fff;
  }
}
</style>