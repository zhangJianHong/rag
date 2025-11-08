<template>
  <div class="activity-chart">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const chartCanvas = ref(null)

const drawChart = () => {
  if (!chartCanvas.value || !props.data.length) return

  const ctx = chartCanvas.value.getContext('2d')
  const width = chartCanvas.value.width = chartCanvas.value.offsetWidth
  const height = chartCanvas.value.height = 200

  // 清空画布
  ctx.clearRect(0, 0, width, height)

  // 设置样式
  const gradient = ctx.createLinearGradient(0, 0, 0, height)
  gradient.addColorStop(0, 'rgba(0, 212, 255, 0.3)')
  gradient.addColorStop(1, 'rgba(0, 212, 255, 0)')

  // 找出最大值
  const maxValue = Math.max(...props.data.map(d => d.value))
  const padding = 20
  const barWidth = (width - padding * 2) / props.data.length
  const scale = (height - padding * 2) / maxValue

  // 绘制条形
  props.data.forEach((item, index) => {
    const x = padding + index * barWidth
    const barHeight = item.value * scale
    const y = height - padding - barHeight

    // 绘制条形
    ctx.fillStyle = gradient
    ctx.fillRect(x + barWidth * 0.2, y, barWidth * 0.6, barHeight)

    // 绘制边框
    ctx.strokeStyle = '#00d4ff'
    ctx.lineWidth = 1
    ctx.strokeRect(x + barWidth * 0.2, y, barWidth * 0.6, barHeight)

    // 绘制标签
    ctx.fillStyle = '#9ca3af'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(item.date, x + barWidth * 0.5, height - 5)

    // 绘制数值
    ctx.fillStyle = '#f3f4f6'
    ctx.fillText(item.value, x + barWidth * 0.5, y - 5)
  })

  // 绘制网格线
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
  ctx.lineWidth = 0.5
  for (let i = 0; i <= 5; i++) {
    const y = padding + (height - padding * 2) * i / 5
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(width - padding, y)
    ctx.stroke()
  }
}

onMounted(() => {
  drawChart()
  // 监听窗口大小变化
  window.addEventListener('resize', drawChart)
})

watch(() => props.data, drawChart, { deep: true })
</script>

<style lang="scss" scoped>
.activity-chart {
  width: 100%;
  height: 200px;

  canvas {
    width: 100%;
    height: 100%;
  }
}
</style>