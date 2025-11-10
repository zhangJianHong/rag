<template>
  <div class="input-bar">
    <div class="input-container">
      <el-input
        v-model="localValue"
        type="textarea"
        :placeholder="placeholder"
        :disabled="disabled"
        :rows="3"
        @keydown.enter.prevent="handleEnter"
        class="tech-textarea"
      />
      <div class="actions">
        <el-button
          v-if="!isGenerating"
          @click="sendMessage"
          :disabled="disabled || !localValue.trim()"
          type="primary"
          circle
          class="send-button"
        >
          <el-icon><Promotion /></el-icon>
        </el-button>
        <el-button
          v-else
          @click="$emit('stop')"
          type="danger"
          circle
          class="stop-button"
        >
          <el-icon><VideoPause /></el-icon>
        </el-button>
      </div>
    </div>
    <div class="input-tips">
      <span class="tip">Enter 发送 / Shift+Enter 换行</span>
      <span class="char-count">{{ charCount }}/4000</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Promotion, VideoPause } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  isGenerating: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: '输入您的问题...'
  }
})

const emit = defineEmits(['update:modelValue', 'send', 'stop'])

const localValue = ref(props.modelValue)

watch(() => props.modelValue, (newVal) => {
  localValue.value = newVal
})

watch(localValue, (newVal) => {
  emit('update:modelValue', newVal)
})

const charCount = computed(() => localValue.value.length)

const handleEnter = (e) => {
  if (!e.shiftKey && localValue.value.trim()) {
    e.preventDefault()
    sendMessage()
  }
}

const sendMessage = () => {
  if (localValue.value.trim() && !props.disabled) {
    emit('send')
  }
}
</script>

<style lang="scss" scoped>
.input-bar {
  background: transparent;
  padding: 0;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  position: relative;
}

:deep(.tech-textarea) {
  flex: 1;

  .el-textarea__inner {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--tech-glass-border);
    color: var(--tech-text-primary);
    backdrop-filter: blur(10px);
    resize: none;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 14px;
    line-height: 1.5;
    transition: all 0.3s ease;

    &:hover {
      background: rgba(255, 255, 255, 0.05);
      border-color: var(--tech-border-hover);
    }

    &:focus {
      background: rgba(255, 255, 255, 0.05);
      border-color: var(--tech-neon-blue);
      box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.1), 0 0 20px rgba(0, 212, 255, 0.15);
    }

    &::placeholder {
      color: var(--tech-text-muted);
    }
  }
}

.actions {
  .send-button,
  .stop-button {
    width: 44px;
    height: 44px;
    transition: all 0.3s ease;
  }

  .send-button {
    background: linear-gradient(135deg, var(--tech-neon-blue), var(--tech-neon-purple));
    border: 1px solid var(--tech-neon-blue);
    box-shadow: 0 4px 12px rgba(0, 212, 255, 0.25);

    &:hover:not(:disabled) {
      transform: translateY(-2px) scale(1.05);
      box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
    }

    &:active:not(:disabled) {
      transform: translateY(0) scale(0.98);
    }

    &:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
  }

  .stop-button {
    background: linear-gradient(135deg, var(--tech-neon-pink), #f5576c);
    border: 1px solid var(--tech-neon-pink);
    box-shadow: 0 4px 12px rgba(236, 72, 153, 0.25);

    &:hover {
      transform: translateY(-2px) scale(1.05);
      box-shadow: 0 6px 20px rgba(236, 72, 153, 0.4);
    }

    &:active {
      transform: translateY(0) scale(0.98);
    }
  }
}

.input-tips {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding: 0 4px;

  .tip {
    font-size: 11px;
    color: var(--tech-text-muted);
    opacity: 0.8;
  }

  .char-count {
    font-size: 11px;
    color: var(--tech-text-muted);
    opacity: 0.6;
  }
}
</style>