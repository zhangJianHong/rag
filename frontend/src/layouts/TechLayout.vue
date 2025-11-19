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
          <div class="flex items-center space-x-4">
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
            <h2 class="tech-title text-sm font-bold" style=" margin-left: 10px; color: #00d4ff; text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);">
              RAG Intelligence System
            </h2>
          </div>
        </div>

        <!-- 右侧工具栏 -->
        <div class="flex items-center space-x-4">
          <!-- 时间显示 -->
          <div class="tech-time text-sm text-gray-400" style="margin-right: 20px;" >
            {{ currentTime }}
          </div>
          <!-- 用户信息 -->
          <el-dropdown @command="handleUserMenuCommand" trigger="click">
            <div class="tech-user flex items-center space-x-2 cursor-pointer hover:bg-white/5 p-2 rounded-lg transition-all">
              <div class="avatar-container-header">
                <div class="tech-avatar-header" :class="roleAvatarClass">
                  <span class="avatar-text-header">{{ userInitial }}</span>
                  <div class="avatar-ring-header"></div>
                </div>
                <div class="absolute -bottom-1 -right-1 w-3 h-3 rounded-full" :class="userStatusDotClass"></div>
              </div>
              <div class="text-left">
                <div class="text-gray-300 text-sm font-medium">{{ authStore.user?.username || 'Unknown' }}</div>
                <!-- <div class="text-gray-500 text-xs" :class="roleTextClass">{{ roleText }}</div> -->
              </div>
              <i class="el-icon-arrow-down text-gray-400 text-xs"></i>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="tech-dropdown">
                <el-dropdown-item command="profile" class="dropdown-item">
                  <i class="el-icon-user mr-2"></i>个人中心
                </el-dropdown-item>
                <el-dropdown-item command="settings" v-if="authStore.hasPermission('system_settings')" class="dropdown-item">
                  <i class="el-icon-setting mr-2"></i>系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout" class="dropdown-item logout-item">
                  <i class="el-icon-switch-button mr-2"></i>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-container>
        <!-- 侧边栏 -->
        <el-aside class="tech-sidebar" :style="sidebarStyle">
          <div class="flex flex-col h-full">
            <!-- 侧边栏头部（切换按钮和菜单在同一行） -->
            <div class="sidebar-header">
              <button
                @click="toggleSidebar"
                class="sidebar-toggle-btn"
                :title="isCollapsed ? '展开菜单' : '收起菜单'"
              >
                <el-icon :size="18" class="toggle-icon">
                  <ArrowRight v-if="isCollapsed" />
                  <ArrowLeft v-else />
                </el-icon>
              </button>
            </div>

            <!-- 导航菜单 -->
            <nav class="flex-1">
              <router-link
                v-for="item in menuItems"
                :key="item.path"
                :to="item.path"
                class="tech-nav-item"
                :class="{ 'active': $route.path === item.path, 'collapsed': isCollapsed }"
                :title="isCollapsed ? item.title : ''"
              >
                <el-icon :size="18" class="nav-icon flex-shrink-0">
                  <component :is="item.icon" />
                </el-icon>
                <transition name="text-fade">
                  <span v-show="!isCollapsed" class="nav-text ml-3">{{ item.title }}</span>
                </transition>
                <transition name="indicator-fade">
                  <div v-show="!isCollapsed" class="nav-indicator"></div>
                </transition>
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
          <span class="status-dot" :class="apiStatusDotClass">●</span>
          <span class="status-text" :class="statusClass">{{ statusText }}</span>
        </div>
        <div class="status-divider"></div>
        <div class="status-item">
          <span class="status-text blue">⏱ 响应时间: {{ responseTime }}ms</span>
        </div>
        <div class="status-divider"></div>
        <div class="status-item">
          <span class="status-text purple">⏰ 运行时间: {{ formattedUptime }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  ChatDotRound,
  Setting,
  Clock,
  HomeFilled,
  DataAnalysis,
  ArrowLeft,
  ArrowRight,
  User,
  FolderOpened,
  Connection,
  Monitor
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { useSystemStatus } from '@/composables/useSystemStatus'

const router = useRouter()
const authStore = useAuthStore()

// 系统状态监控
const {
  statusText,
  statusClass,
  statusDotClass: apiStatusDotClass,
  responseTime,
  formattedUptime
} = useSystemStatus()

// 侧边栏展开/收起控制
const isCollapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')

// 计算侧边栏的样式
const sidebarStyle = computed(() => {
  return {
    width: isCollapsed.value ? '4rem' : '16rem',
    transition: 'all 0.3s ease-in-out'
  }
})

// 切换侧边栏状态
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
  // 持久化状态到本地存储
  localStorage.setItem('sidebar-collapsed', isCollapsed.value.toString())
}

// 菜单项配置（根据权限动态生成）
const menuItems = computed(() => {
  const items = []

  // 基础菜单项
  items.push({ path: '/dashboard', title: '仪表盘', icon: HomeFilled })

  // 根据权限添加菜单项
  if (authStore.hasPermission('query_ask')) {
    items.push({ path: '/chat', title: '智能对话', icon: ChatDotRound })
  }

  if (authStore.hasPermission('document_read')) {
    items.push({ path: '/documents', title: '文档管理', icon: Document })
  }

  if (authStore.hasPermission('query_history')) {
    items.push({ path: '/history', title: '查询历史', icon: Clock })
  }

  if (authStore.hasPermission('system_settings')) {
    items.push({ path: '/performance', title: '性能监控', icon: Monitor })
    items.push({ path: '/knowledge-domains', title: '知识领域', icon: FolderOpened })
    items.push({ path: '/routing-rules', title: '路由规则', icon: Connection })
    items.push({ path: '/logs', title: '系统日志', icon: DataAnalysis })
    items.push({ path: '/settings', title: '系统设置', icon: Setting })
  }

  if (authStore.hasPermission('user_management')) {
    items.push({ path: '/user-management', title: '用户管理', icon: User })
  }

  return items
})

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

// 用户相关计算属性
const userInitial = computed(() => {
  const username = authStore.user?.username || 'U'
  return username.charAt(0).toUpperCase()
})

const roleText = computed(() => {
  const role = authStore.user?.role || 'user'
  switch (role) {
    case 'admin':
      return '管理员'
    case 'user':
      return '普通用户'
    case 'readonly':
      return '只读用户'
    default:
      return '用户'
  }
})

const roleTextClass = computed(() => {
  const role = authStore.user?.role || 'user'
  switch (role) {
    case 'admin':
      return 'text-red-400'
    case 'user':
      return 'text-blue-400'
    case 'readonly':
      return 'text-green-400'
    default:
      return 'text-gray-400'
  }
})

const roleAvatarClass = computed(() => {
  const role = authStore.user?.role || 'user'
  switch (role) {
    case 'admin':
      return 'avatar-admin'
    case 'user':
      return 'avatar-user'
    case 'readonly':
      return 'avatar-readonly'
    default:
      return 'avatar-default'
  }
})

const userStatusDotClass = computed(() => {
  const role = authStore.user?.role || 'user'
  switch (role) {
    case 'admin':
      return 'bg-red-500'
    case 'user':
      return 'bg-blue-500'
    case 'readonly':
      return 'bg-green-500'
    default:
      return 'bg-gray-500'
  }
})

// 处理用户菜单命令
const handleUserMenuCommand = async (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '退出确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await authStore.logout()
        ElMessage.success('已安全退出')
        router.push('/login')
      } catch (error) {
        // 用户取消操作
      }
      break
  }
}

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
    padding: 12px;
    margin-bottom: 4px;
    border-radius: 8px;
    color: var(--tech-text-secondary);
    text-decoration: none;
    position: relative;
    transition: all 0.3s ease;
    overflow: hidden;
    justify-content: flex-start;

    // 收起状态下的样式
    &.collapsed {
      justify-content: center;
      padding: 12px 8px;
    }

    .nav-icon {
      transition: all 0.3s ease;
      flex-shrink: 0;
    }

    .nav-text {
      font-size: 14px;
      white-space: nowrap;
      transition: all 0.3s ease;
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
      transform: translateX(2px);
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

  // 侧边栏头部样式
  .sidebar-header {
    padding: 12px;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  // 切换按钮样式
  .sidebar-toggle-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 12px;
    border-radius: 8px;
    color: var(--tech-text-secondary);
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
    cursor: pointer;

    &:hover {
      color: var(--tech-text-primary);
      background: rgba(0, 212, 255, 0.05);
      border-color: rgba(0, 212, 255, 0.3);
      transform: translateX(2px);
    }

    .toggle-icon {
      transition: all 0.3s ease;
    }

    &:hover .toggle-icon {
      color: var(--tech-neon-blue);
      transform: scale(1.1);
    }
  }

  // 侧边栏收起状态下的头部
  &.collapsed .sidebar-header {
    padding: 12px 8px;
  }

  // 侧边栏收起状态下的按钮
  &.collapsed .sidebar-toggle-btn {
    padding: 12px 0;
  }
}

// 文本和指示器的过渡动画
.text-fade-enter-active,
.text-fade-leave-active {
  transition: all 0.2s ease;
}

.text-fade-enter-from,
.text-fade-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.indicator-fade-enter-active,
.indicator-fade-leave-active {
  transition: all 0.2s ease;
}

.indicator-fade-enter-from,
.indicator-fade-leave-to {
  opacity: 0;
  transform: scale(0.5);
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

// 用户头像样式
.avatar-container-header {
  position: relative;
}

.tech-avatar-header {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.3s ease;
}

.tech-avatar-header.avatar-admin {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
}

.tech-avatar-header.avatar-user {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
}

.tech-avatar-header.avatar-readonly {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
}

.tech-avatar-header.avatar-default {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  box-shadow: 0 0 20px rgba(107, 114, 128, 0.5);
}

.avatar-text-header {
  font-size: 14px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  z-index: 1;
}

.avatar-ring-header {
  position: absolute;
  top: -3px;
  left: -3px;
  right: -3px;
  bottom: -3px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  animation: ring-rotate 10s linear infinite;
}

@keyframes ring-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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

// 用户下拉菜单样式
:deep(.tech-dropdown) {
  background: var(--tech-glass-bg);
  backdrop-filter: var(--tech-backdrop-blur);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  padding: 8px;
  min-width: 160px;

  .dropdown-item {
    color: var(--tech-text-secondary);
    padding: 10px 16px;
    border-radius: 8px;
    transition: all var(--tech-transition-fast);
    margin: 2px 0;

    &:hover {
      background: rgba(0, 212, 255, 0.1);
      color: var(--tech-neon-blue);
    }

    &.logout-item {
      color: var(--tech-neon-pink);

      &:hover {
        background: rgba(236, 72, 153, 0.1);
        color: var(--tech-neon-pink);
      }
    }

    i {
      font-size: 14px;
      opacity: 0.8;
    }
  }

  .el-dropdown-menu__item--divided {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    margin-top: 4px;
    padding-top: 8px;
  }
}

// 响应式
@media (max-width: 1024px) {
  .tech-sidebar {
    // 在平板和移动端默认收起
    &.w-64 {
      width: 4rem !important;
    }

    &.w-16 {
      width: 4rem !important;
    }

    .tech-nav-item {
      justify-content: center;
      padding: 12px 8px;

      .nav-text {
        display: none;
      }

      .nav-indicator {
        display: none;
      }
    }

    .sidebar-toggle {
      // 在移动端隐藏切换按钮，保持收起状态
      display: none;
    }
  }
}

@media (max-width: 768px) {
  .tech-header {
    padding: 0 1rem;

    .tech-title {
      font-size: 1rem;
    }
  }

  .tech-main {
    height: calc(100vh - 64px - 50px);
  }

  .status-bar {
    padding: 0 1rem;

    .status-content {
      gap: 12px;
    }

    .status-text {
      font-size: 12px;

      &.blue,
      &.purple {
        display: none;
      }
    }
  }
}

@media (max-width: 480px) {
  .status-bar {
    .status-content {
      gap: 8px;
    }

    .status-item:not(:first-child) {
      display: none;
    }
  }
}
</style>