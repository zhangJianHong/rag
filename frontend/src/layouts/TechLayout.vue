<template>
  <div class="tech-layout">
    <!-- 动态网格背景 -->
    <div class="tech-grid-bg"></div>

    <!-- 主容器 -->
    <el-container class="h-screen relative z-10">
      <!-- 顶栏 -->
      <el-header class="tech-header h-16 flex items-center justify-between px-6">
        <div class="flex items-center space-x-4">
          <!-- Logo和标题 -->
          <div class="flex items-center space-x-3">
            <div class="tech-logo">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <path d="M16 2L2 9L16 16L30 9L16 2Z" stroke="var(--tech-neon-blue)" stroke-width="2" fill="url(#logo-gradient)"/>
                <path d="M2 23L16 30L30 23" stroke="var(--tech-neon-purple)" stroke-width="2"/>
                <path d="M2 16L16 23L30 16" stroke="var(--tech-neon-blue)" stroke-width="2" opacity="0.6"/>
                <defs>
                  <linearGradient id="logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="var(--tech-neon-blue)" stop-opacity="0.2"/>
                    <stop offset="100%" stop-color="var(--tech-neon-purple)" stop-opacity="0.2"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <h1 class="tech-title text-xl font-bold" style="color: #00d4ff; text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);">
              RAG Intelligence System
            </h1>
          </div>
        </div>

        <!-- 右侧工具栏 -->
        <div class="flex items-center space-x-4">
          <!-- 时间显示 -->
          <div class="tech-time text-sm text-gray-400">
            {{ currentTime }}
          </div>
          <!-- 用户信息 -->
          <div class="tech-user flex items-center space-x-2">
            <div class="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
              <span class="text-white text-sm">U</span>
            </div>
            <span class="text-gray-300 text-sm">User</span>
          </div>
        </div>
      </el-header>

      <el-container>
        <!-- 侧边栏 -->
        <el-aside class="tech-sidebar w-64">
          <div class="p-4">
            <!-- 导航菜单 -->
            <nav class="space-y-2">
              <router-link
                v-for="item in menuItems"
                :key="item.path"
                :to="item.path"
                class="tech-nav-item"
                :class="{ 'active': $route.path === item.path }"
              >
                <el-icon :size="18" class="nav-icon">
                  <component :is="item.icon" />
                </el-icon>
                <span class="nav-text">{{ item.title }}</span>
                <div class="nav-indicator"></div>
              </router-link>
            </nav>
          </div>
        </el-aside>

        <!-- 主内容区 -->
        <el-main class="tech-main">
          <div class="tech-content">
            <!-- 路由视图 -->
            <transition name="fade-transform" mode="out-in">
              <router-view />
            </transition>
          </div>
        </el-main>
      </el-container>
    </el-container>

    <!-- 底部状态条 -->
    <div class="status-bar">
      <div class="status-content">
        <div class="status-item">
          <span class="status-dot">●</span>
          <span class="status-text">API 正常</span>
        </div>
        <div class="status-divider"></div>
        <div class="status-item">
          <span class="status-text blue">⏱ 响应时间: 2.3ms</span>
        </div>
        <div class="status-divider"></div>
        <div class="status-item">
          <span class="status-text purple">⏰ 运行时间: 02:45:12</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Document,
  ChatDotRound,
  Setting,
  Clock,
  HomeFilled,
  CircleCheck,
  Timer
} from '@element-plus/icons-vue'

const route = useRoute()

// 菜单项配置
const menuItems = [
  { path: '/', title: '控制台', icon: HomeFilled },
  { path: '/chat', title: '智能对话', icon: ChatDotRound },
  { path: '/documents', title: '文档管理', icon: Document },
  { path: '/history', title: '历史记录', icon: Clock },
  { path: '/settings', title: '系统配置', icon: Setting },
]

// 时间显示
const currentTime = ref('')
let timeInterval = null

const updateTime = () => {
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${hours}:${minutes}:${seconds}`
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style lang="scss" scoped>
.tech-layout {
  min-height: 100vh;
  background: var(--tech-bg-primary);
  position: relative;
  overflow: hidden;
}

// 顶栏样式
.tech-header {
  background: rgba(17, 24, 39, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  z-index: 100;

  .tech-logo {
    animation: pulse-glow 3s infinite;
  }
}

// 侧边栏样式
.tech-sidebar {
  background: rgba(17, 24, 39, 0.6);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;

  .tech-nav-item {
    display: flex;
    align-items: center;
    padding: 10px 14px;
    border-radius: 8px;
    color: var(--tech-text-secondary);
    text-decoration: none;
    position: relative;
    transition: all 0.3s ease;
    overflow: hidden;

    .nav-icon {
      margin-right: 10px;
      flex-shrink: 0;
    }

    .nav-text {
      font-size: 14px;
      flex: 1;
    }

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: linear-gradient(180deg, var(--tech-neon-blue), var(--tech-neon-purple));
      transform: translateX(-100%);
      transition: transform 0.3s ease;
    }

    &:hover {
      color: var(--tech-text-primary);
      background: rgba(0, 212, 255, 0.05);
    }

    &.active {
      color: var(--tech-neon-blue);
      background: rgba(0, 212, 255, 0.1);

      &::before {
        transform: translateX(0);
      }

      .nav-indicator {
        opacity: 1;
      }
    }

    .nav-indicator {
      position: absolute;
      right: 16px;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--tech-neon-blue);
      opacity: 0;
      transition: opacity 0.3s ease;
      animation: pulse-glow 2s infinite;
    }
  }
}

// 主内容区样式
.tech-main {
  background: transparent;
  padding: 0;
  position: relative;
  height: calc(100vh - 64px - 50px); // 减去header和status bar高度
  overflow: auto;
  margin-bottom: 50px; // 给状态条留空间

  .tech-content {
    height: 100%;
    max-width: 100%;
    margin: 0;
    position: relative;
    overflow: hidden;
  }
}

// 过渡动画
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

// 状态条发光动画
@keyframes status-glow {
  0%, 100% {
    opacity: 0;
  }
  50% {
    opacity: 0.6;
  }
}

// 状态条样式
.status-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50px;
  background: #0f172a;
  border-top: 3px solid #00d4ff;
  display: flex;
  align-items: center;
  padding: 0 30px;
  z-index: 9999;
  box-shadow: 0 -2px 20px rgba(0, 212, 255, 0.4);

  .status-content {
    display: flex;
    align-items: center;
    gap: 24px;
    width: 100%;
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .status-dot {
    color: #00ff00;
    font-size: 18px;
    text-shadow: 0 0 8px rgba(0, 255, 0, 0.6);
  }

  .status-text {
    color: #ffffff;
    font-size: 14px;
    font-weight: 500;

    &.blue {
      color: #00d4ff;
    }

    &.purple {
      color: #a855f7;
    }
  }

  .status-divider {
    width: 1px;
    height: 20px;
    background: rgba(255, 255, 255, 0.3);
  }
}

// 响应式
@media (max-width: 768px) {
  .tech-sidebar {
    width: 200px;
  }
}
</style>