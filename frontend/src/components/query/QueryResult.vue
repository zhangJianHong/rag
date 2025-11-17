<template>
  <div class="query-result">
    <!-- 查询信息头部 -->
    <div class="query-header" v-if="result">
      <div class="query-info">
        <h3 class="query-text">{{ result.query }}</h3>
        <div class="query-meta">
          <el-tag :type="getModeTagType(result.retrievalMode)" size="small">
            {{ getModeInfo(result.retrievalMode).name }}
          </el-tag>
          <el-tag :type="getMethodTagType(result.retrievalMethod)" size="small">
            {{ getMethodInfo(result.retrievalMethod).name }}
          </el-tag>
          <span class="latency">{{ result.stats.latencyMs.toFixed(0) }}ms</span>
          <span class="count">{{ result.stats.totalCandidates }} 个结果</span>
        </div>
      </div>

      <!-- 领域分类信息 -->
      <div class="classification-info" v-if="result.classification">
        <div class="classification-badge">
          <DomainBadge
            :namespace="result.classification.namespace"
            :display-name="result.classification.displayName"
          />
          <el-tag
            :type="getConfidenceLevelType(result.classification.confidence)"
            size="small"
            class="confidence-tag"
          >
            置信度: {{ (result.classification.confidence * 100).toFixed(0) }}%
          </el-tag>
        </div>

        <!-- 备选领域 -->
        <div class="alternatives" v-if="result.classification.alternatives?.length > 0">
          <span class="alternatives-label">备选:</span>
          <DomainBadge
            v-for="alt in result.classification.alternatives.slice(0, 3)"
            :key="alt.namespace"
            :namespace="alt.namespace"
            :display-name="alt.display_name"
            size="small"
          />
        </div>
      </div>
    </div>

    <!-- 跨领域分组结果 -->
    <div class="cross-domain-results" v-if="result?.crossDomainResults">
      <CrossDomainGroups :groups="result.crossDomainResults" :query="result.query" />
    </div>

    <!-- 统一结果列表 -->
    <div class="results-list" v-if="result?.results?.length > 0">
      <div
        v-for="(chunk, index) in result.results"
        :key="chunk.chunkId"
        class="result-item"
      >
        <div class="result-header">
          <span class="result-index">#{{ index + 1 }}</span>
          <DomainBadge
            :namespace="chunk.namespace"
            :display-name="chunk.domainDisplayName"
            :color="chunk.domainColor"
            size="small"
          />
          <el-tag type="info" size="small" class="score-tag">
            {{ (chunk.score * 100).toFixed(1) }}%
          </el-tag>
        </div>

        <div class="result-content">
          <p class="content-text" v-html="highlightText(chunk.content, result.query)"></p>
        </div>

        <div class="result-footer">
          <span class="document-title">
            <el-icon><Document /></el-icon>
            {{ chunk.documentTitle }}
          </span>
          <span class="chunk-index" v-if="chunk.chunkIndex !== null">
            块 #{{ chunk.chunkIndex }}
          </span>
        </div>
      </div>
    </div>

    <!-- 空结果提示 -->
    <el-empty
      v-if="result && result.results.length === 0"
      description="未找到相关内容"
      :image-size="120"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Document } from '@element-plus/icons-vue'
import DomainBadge from '../domain/DomainBadge.vue'
import CrossDomainGroups from './CrossDomainGroups.vue'
import {
  getMethodInfo,
  getModeInfo,
  highlightKeywords,
  getConfidenceLevel
} from '@/services/queryService'

const props = defineProps({
  result: {
    type: Object,
    default: null
  }
})

// 高亮文本
const highlightText = (text, query) => {
  return highlightKeywords(text, query)
}

// 获取模式标签类型
const getModeTagType = (mode) => {
  const typeMap = {
    auto: 'primary',
    single: 'success',
    cross: 'warning'
  }
  return typeMap[mode] || 'info'
}

// 获取方法标签类型
const getMethodTagType = (method) => {
  const typeMap = {
    vector: 'primary',
    bm25: 'warning',
    hybrid: 'success'
  }
  return typeMap[method] || 'info'
}

// 获取置信度等级类型
const getConfidenceLevelType = (confidence) => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'danger'
}
</script>

<style lang="scss" scoped>
.query-result {
  width: 100%;
}

.query-header {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  backdrop-filter: blur(10px);

  .query-info {
    margin-bottom: 16px;

    .query-text {
      font-size: 18px;
      font-weight: 600;
      color: var(--tech-text-primary);
      margin: 0 0 12px 0;
      background: linear-gradient(135deg, var(--tech-neon-blue), var(--tech-neon-purple));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .query-meta {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 14px;
      color: var(--tech-text-secondary);

      .el-tag {
        border: 1px solid var(--tech-glass-border);
        background: rgba(255, 255, 255, 0.05);
      }

      .latency,
      .count {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 4px 12px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--tech-glass-border);
        border-radius: 4px;
      }
    }
  }

  .classification-info {
    padding-top: 16px;
    border-top: 1px solid var(--tech-glass-border);

    .classification-badge {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;

      .confidence-tag {
        border: 1px solid var(--tech-glass-border);
        background: rgba(255, 255, 255, 0.05);
      }
    }

    .alternatives {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;

      .alternatives-label {
        font-size: 13px;
        color: var(--tech-text-secondary);
      }
    }
  }
}

.cross-domain-results {
  margin-bottom: 24px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .result-item {
    background: var(--tech-glass-bg);
    border: 1px solid var(--tech-glass-border);
    border-radius: 12px;
    padding: 16px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: linear-gradient(180deg, var(--tech-neon-blue), var(--tech-neon-purple));
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    &:hover {
      border-color: var(--tech-border-hover);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

      &::before {
        opacity: 1;
      }
    }

    .result-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;

      .result-index {
        font-size: 14px;
        font-weight: 600;
        color: var(--tech-neon-blue);
        min-width: 30px;
      }

      .score-tag {
        margin-left: auto;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--tech-glass-border);
        font-weight: 600;
      }
    }

    .result-content {
      margin-bottom: 12px;

      .content-text {
        font-size: 14px;
        line-height: 1.6;
        color: var(--tech-text-primary);
        margin: 0;

        :deep(mark.highlight) {
          background: rgba(0, 212, 255, 0.2);
          color: var(--tech-neon-blue);
          padding: 2px 4px;
          border-radius: 2px;
          font-weight: 600;
        }
      }
    }

    .result-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 13px;
      color: var(--tech-text-secondary);

      .document-title {
        display: flex;
        align-items: center;
        gap: 6px;

        .el-icon {
          font-size: 14px;
        }
      }

      .chunk-index {
        padding: 2px 8px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--tech-glass-border);
        border-radius: 4px;
        font-size: 12px;
      }
    }
  }
}

:deep(.el-empty) {
  padding: 60px 0;

  .el-empty__description p {
    color: var(--tech-text-secondary);
  }
}
</style>
