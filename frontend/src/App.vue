<template>
  <div id="app">
    <TechLayout />
  </div>
</template>

<script setup>
import TechLayout from './layouts/TechLayout.vue'
</script>

<style>
body {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--tech-bg-primary);
  color: var(--tech-text-primary);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  height: 100vh;
  overflow: hidden;
}
</style>