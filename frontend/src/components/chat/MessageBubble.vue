<template>
  <div class="message-bubble" :class="messageClass">
    <div class="message-content">
      <!-- 头像 -->
      <div class="avatar">
        <el-icon v-if="message.role === 'user'" class="text-xl"><User /></el-icon>
        <el-icon v-else class="text-xl"><Monitor /></el-icon>
      </div>

      <!-- 消息内容 -->
      <div class="content">
        <div class="text" v-if="message.content" v-html="renderedContent"></div>
        <!-- 加载动画 - 当消息为空且是助手消息时显示 -->
        <div v-else-if="message.role === 'assistant' && !message.content" class="loading-dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
        <div class="meta">
          <span class="time">{{ formatTime(message.timestamp) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { User, Monitor } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const md = new MarkdownIt({
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return ''
  }
})

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  isLast: {
    type: Boolean,
    default: false
  }
})

const messageClass = computed(() => ({
  'user-message': props.message.role === 'user',
  'assistant-message': props.message.role === 'assistant',
  'is-last': props.isLast
}))

const renderedContent = computed(() => {
  if (props.message.role === 'assistant') {
    return md.render(props.message.content)
  }
  return props.message.content.replace(/\n/g, '<br>')
})

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.message-bubble {
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease;

  &.user-message {
    .message-content {
      flex-direction: row-reverse;
    }

    .content {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
      border: 1px solid rgba(102, 126, 234, 0.3);
      margin-right: 12px;
      margin-left: auto;
      max-width: 70%;
    }
  }

  &.assistant-message {
    .content {
      background: var(--tech-glass-bg);
      border: 1px solid var(--tech-glass-border);
      margin-left: 12px;
      max-width: 80%;
    }
  }
}

.message-content {
  display: flex;
  align-items: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--tech-neon-blue) 0%, var(--tech-neon-purple) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.content {
  padding: 12px 16px;
  border-radius: 12px;
  backdrop-filter: blur(10px);

  .text {
    color: var(--tech-text-primary);
    line-height: 1.6;

    :deep(pre) {
      background: var(--tech-bg-secondary);
      padding: 12px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 8px 0;
    }

    :deep(code) {
      background: rgba(0, 212, 255, 0.1);
      padding: 2px 6px;
      border-radius: 4px;
      color: var(--tech-neon-blue);
    }
  }

  .meta {
    margin-top: 8px;
    font-size: 12px;
    color: var(--tech-text-muted);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 加载动画
.loading-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--tech-text-muted);
    animation: typing 1.4s ease-in-out infinite;

    &:nth-child(1) {
      animation-delay: 0s;
    }

    &:nth-child(2) {
      animation-delay: 0.2s;
    }

    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.3;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}
</style>