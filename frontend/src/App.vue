<template>
  <div id="app">
    <el-container>
      <el-header style="background-color: #409EFF; color: white;">
        <h1 style="margin: 0; line-height: 60px;">RAG 智能问答系统</h1>
      </el-header>
      
      <el-container>
        <el-aside width="200px" style="background-color: #f5f7fa;">
          <el-menu
            :default-active="$route.path"
            router
            style="height: 100%; border-right: none;"
          >
            <el-menu-item index="/">
              <el-icon><Document /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/history">
              <el-icon><Clock /></el-icon>
              <span>查询历史</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { Document, Clock } from '@element-plus/icons-vue'
</script>

<style>
body {
  margin: 0;
  font-family: Arial, sans-serif;
}

#app {
  height: 100vh;
}

.el-container {
  height: 100%;
}

.el-aside {
  border-right: 1px solid #e4e7ed;
}
</style>