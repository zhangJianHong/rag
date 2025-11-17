<template>
  <div class="knowledge-domains-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div>
          <h1 class="page-title">🗂️ 知识领域管理</h1>
          <p class="page-subtitle">管理多领域知识库,实现知识分类和精准检索</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建领域
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon primary">
          <el-icon><FolderOpened /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ totalDomains }}</div>
          <div class="stat-label">总领域数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ activeDomains }}</div>
          <div class="stat-label">启用领域</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon warning">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ totalDocuments }}</div>
          <div class="stat-label">总文档数</div>
        </div>
      </div>
    </div>

    <!-- 领域列表 -->
    <div class="domains-container">
      <el-card class="domains-card" shadow="hover">
        <!-- 工具栏 -->
        <div class="toolbar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索领域..."
            :prefix-icon="Search"
            style="width: 300px"
            clearable
            @input="handleSearch"
          />
          <div class="toolbar-actions">
            <el-switch
              v-model="showInactive"
              active-text="显示未启用"
              @change="loadDomains"
            />
          </div>
        </div>

        <!-- 表格 -->
        <el-table
          v-loading="loading"
          :data="filteredDomains"
          style="width: 100%"
          :default-sort="{ prop: 'priority', order: 'descending' }"
        >
          <el-table-column prop="namespace" label="命名空间" width="180">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ row.namespace }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="领域信息" min-width="250">
            <template #default="{ row }">
              <div class="domain-info">
                <div class="domain-name">
                  <el-icon v-if="row.icon" :size="18" :style="{ color: row.color }">
                    <component :is="getIcon(row.icon)" />
                  </el-icon>
                  <span>{{ row.display_name }}</span>
                </div>
                <div class="domain-desc">{{ row.description }}</div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="keywords" label="关键词" width="200">
            <template #default="{ row }">
              <el-tag
                v-for="(keyword, index) in row.keywords.slice(0, 3)"
                :key="index"
                size="small"
                type="info"
                class="keyword-tag"
              >
                {{ keyword }}
              </el-tag>
              <el-tag v-if="row.keywords.length > 3" size="small" type="info">
                +{{ row.keywords.length - 3 }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="统计" width="150" align="center">
            <template #default="{ row }">
              <div class="domain-stats">
                <div class="stat-item">
                  <el-icon><Document /></el-icon>
                  <span>{{ row.document_count || 0 }}</span>
                </div>
                <div class="stat-item">
                  <el-icon><Files /></el-icon>
                  <span>{{ row.chunk_count || 0 }}</span>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="priority" label="优先级" width="100" align="center" sortable />

          <el-table-column prop="is_active" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                @change="handleToggleActive(row)"
              />
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                text
                @click="handleEdit(row)"
              >
                编辑
              </el-button>
              <el-button
                type="info"
                size="small"
                text
                @click="handleViewStats(row)"
              >
                统计
              </el-button>
              <el-button
                v-if="row.namespace !== 'default'"
                type="danger"
                size="small"
                text
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingDomain ? '编辑领域' : '创建领域'"
      width="600px"
    >
      <el-form
        ref="domainFormRef"
        :model="domainForm"
        :rules="domainFormRules"
        label-width="100px"
      >
        <el-form-item label="命名空间" prop="namespace">
          <el-input
            v-model="domainForm.namespace"
            placeholder="例如: technical_docs"
            :disabled="!!editingDomain"
          />
          <div class="form-tip">只能包含小写字母、数字、下划线和连字符</div>
        </el-form-item>

        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="domainForm.display_name" placeholder="例如: 技术文档" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="domainForm.description"
            type="textarea"
            :rows="3"
            placeholder="领域的详细描述..."
          />
        </el-form-item>

        <el-form-item label="关键词">
          <el-select
            v-model="domainForm.keywords"
            multiple
            filterable
            allow-create
            placeholder="输入关键词后按回车"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="图标">
          <el-select v-model="domainForm.icon" placeholder="选择图标">
            <el-option label="文件夹" value="folder">
              <el-icon><Folder /></el-icon> 文件夹
            </el-option>
            <el-option label="文档" value="document">
              <el-icon><Document /></el-icon> 文档
            </el-option>
            <el-option label="代码" value="code">
              <el-icon><Document /></el-icon> 代码
            </el-option>
            <el-option label="工具" value="tools">
              <el-icon><Tools /></el-icon> 工具
            </el-option>
            <el-option label="支持" value="support">
              <el-icon><Tools /></el-icon> 支持
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="主题色">
          <el-color-picker v-model="domainForm.color" />
          <span class="color-preview" :style="{ backgroundColor: domainForm.color }">
            {{ domainForm.color }}
          </span>
        </el-form-item>

        <el-form-item label="优先级">
          <el-input-number v-model="domainForm.priority" :min="0" :max="100" />
          <div class="form-tip">数值越大优先级越高</div>
        </el-form-item>

        <el-form-item label="启用">
          <el-switch v-model="domainForm.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ editingDomain ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 统计详情对话框 -->
    <el-dialog v-model="showStatsDialog" title="领域统计" width="500px">
      <div v-if="currentStats" class="stats-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="命名空间">
            {{ currentStats.namespace }}
          </el-descriptions-item>
          <el-descriptions-item label="文档数量">
            <el-tag type="primary">{{ currentStats.document_count }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分块数量">
            <el-tag type="success">{{ currentStats.chunk_count }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="平均置信度">
            <el-progress
              :percentage="currentStats.avg_confidence * 100"
              :color="getConfidenceColor(currentStats.avg_confidence)"
            />
          </el-descriptions-item>
          <el-descriptions-item label="最近7天上传">
            <el-tag type="warning">{{ currentStats.recent_uploads }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  FolderOpened,
  CircleCheck,
  Document,
  Files,
  Folder,
  Tools
} from '@element-plus/icons-vue'
import {
  getAllDomains,
  createDomain,
  updateDomain,
  deleteDomain,
  getDomainStats
} from '@/services/knowledgeDomains'

// 状态
const loading = ref(false)
const submitting = ref(false)
const domains = ref([])
const searchKeyword = ref('')
const showInactive = ref(false)
const showCreateDialog = ref(false)
const showStatsDialog = ref(false)
const editingDomain = ref(null)
const currentStats = ref(null)

// 表单
const domainFormRef = ref(null)
const domainForm = ref({
  namespace: '',
  display_name: '',
  description: '',
  keywords: [],
  icon: 'folder',
  color: '#4A90E2',
  priority: 0,
  is_active: true,
  permissions: {},
  metadata: {}
})

// 表单验证规则
const domainFormRules = {
  namespace: [
    { required: true, message: '请输入命名空间', trigger: 'blur' },
    { pattern: /^[a-z0-9_-]+$/, message: '只能包含小写字母、数字、下划线和连字符', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' }
  ]
}

// 统计数据
const totalDomains = computed(() => domains.value.length)
const activeDomains = computed(() => domains.value.filter(d => d.is_active).length)
const totalDocuments = computed(() => {
  return domains.value.reduce((sum, d) => sum + (d.document_count || 0), 0)
})

// 过滤后的领域列表
const filteredDomains = computed(() => {
  if (!searchKeyword.value) return domains.value
  const keyword = searchKeyword.value.toLowerCase()
  return domains.value.filter(d =>
    d.namespace.toLowerCase().includes(keyword) ||
    d.display_name.toLowerCase().includes(keyword) ||
    (d.description && d.description.toLowerCase().includes(keyword))
  )
})

// 获取图标组件
const getIcon = (iconName) => {
  const iconMap = {
    'folder': Folder,
    'document': Document,
    'code': Document,
    'tools': Tools,
    'support': Tools
  }
  return iconMap[iconName] || Folder
}

// 获取置信度颜色
const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#67c23a'
  if (confidence >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

// 加载领域列表
const loadDomains = async () => {
  loading.value = true
  try {
    const response = await getAllDomains({
      include_inactive: showInactive.value,
      with_stats: true
    })
    domains.value = response.domains || []
  } catch (error) {
    ElMessage.error('加载领域列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  // 搜索由 computed 自动处理
}

// 切换启用状态
const handleToggleActive = async (domain) => {
  try {
    await updateDomain(domain.namespace, {
      is_active: domain.is_active
    })
    ElMessage.success('状态已更新')
  } catch (error) {
    domain.is_active = !domain.is_active // 回滚
    ElMessage.error('更新失败')
  }
}

// 编辑领域
const handleEdit = (domain) => {
  editingDomain.value = domain
  domainForm.value = {
    namespace: domain.namespace,
    display_name: domain.display_name,
    description: domain.description || '',
    keywords: domain.keywords || [],
    icon: domain.icon || 'folder',
    color: domain.color || '#4A90E2',
    priority: domain.priority || 0,
    is_active: domain.is_active,
    permissions: domain.permissions || {},
    metadata: domain.metadata || {}
  }
  showCreateDialog.value = true
}

// 查看统计
const handleViewStats = async (domain) => {
  try {
    currentStats.value = await getDomainStats(domain.namespace)
    showStatsDialog.value = true
  } catch (error) {
    ElMessage.error('获取统计信息失败')
  }
}

// 删除领域
const handleDelete = async (domain) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除领域 "${domain.display_name}" 吗?如果有关联文档将无法删除。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteDomain(domain.namespace)
    ElMessage.success('删除成功')
    loadDomains()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!domainFormRef.value) return

  await domainFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (editingDomain.value) {
        // 编辑
        const { namespace, ...updateData } = domainForm.value
        await updateDomain(namespace, updateData)
        ElMessage.success('更新成功')
      } else {
        // 创建
        await createDomain(domainForm.value)
        ElMessage.success('创建成功')
      }

      showCreateDialog.value = false
      editingDomain.value = null
      resetForm()
      loadDomains()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  domainForm.value = {
    namespace: '',
    display_name: '',
    description: '',
    keywords: [],
    icon: 'folder',
    color: '#4A90E2',
    priority: 0,
    is_active: true,
    permissions: {},
    metadata: {}
  }
  editingDomain.value = null
}

// 挂载时加载
onMounted(() => {
  loadDomains()
})
</script>

<style lang="scss" scoped>
.knowledge-domains-page {
  padding: 24px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .page-header {
    margin-bottom: 24px;

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .page-title {
        font-size: 28px;
        font-weight: 600;
        color: white;
        margin: 0 0 8px 0;
      }

      .page-subtitle {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.8);
        margin: 0;
      }

      .header-actions {
        display: flex;
        gap: 12px;
      }
    }
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
    margin-bottom: 24px;

    .stat-card {
      background: white;
      border-radius: 12px;
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;

        &.primary {
          background: #e3f2fd;
          color: #2196f3;
        }

        &.success {
          background: #e8f5e9;
          color: #4caf50;
        }

        &.warning {
          background: #fff3e0;
          color: #ff9800;
        }
      }

      .stat-content {
        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: #333;
        }

        .stat-label {
          font-size: 14px;
          color: #666;
          margin-top: 4px;
        }
      }
    }
  }

  .domains-container {
    .domains-card {
      border-radius: 12px;

      .toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;

        .toolbar-actions {
          display: flex;
          gap: 12px;
          align-items: center;
        }
      }

      .domain-info {
        .domain-name {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
          margin-bottom: 4px;
        }

        .domain-desc {
          font-size: 12px;
          color: #999;
        }
      }

      .keyword-tag {
        margin-right: 4px;
        margin-bottom: 4px;
      }

      .domain-stats {
        display: flex;
        gap: 12px;
        justify-content: center;

        .stat-item {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 14px;
        }
      }
    }
  }

  .form-tip {
    font-size: 12px;
    color: #999;
    margin-top: 4px;
  }

  .color-preview {
    display: inline-block;
    margin-left: 12px;
    padding: 4px 12px;
    border-radius: 4px;
    color: white;
    font-size: 12px;
  }

  .stats-detail {
    margin-top: 20px;
  }
}
</style>
