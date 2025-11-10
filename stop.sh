#!/bin/bash

# RAG 智能问答系统 - 停止脚本
# 功能: 停止前后端服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}RAG 智能问答系统 - 停止程序${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# 停止后端服务
echo -e "${YELLOW}[1/2] 停止后端服务...${NC}"
BACKEND_PIDS=$(lsof -t -i:8800 2>/dev/null || true)
if [ -n "$BACKEND_PIDS" ]; then
    kill $BACKEND_PIDS 2>/dev/null || true
    sleep 2
    # 强制杀死仍在运行的进程
    BACKEND_PIDS=$(lsof -t -i:8800 2>/dev/null || true)
    if [ -n "$BACKEND_PIDS" ]; then
        kill -9 $BACKEND_PIDS 2>/dev/null || true
    fi
    echo -e "${GREEN}   ✅ 后端服务已停止${NC}"
else
    echo -e "${YELLOW}   ℹ️  后端服务未运行${NC}"
fi

# 停止前端服务
echo -e "${YELLOW}[2/2] 停止前端服务...${NC}"
FRONTEND_PIDS=$(lsof -t -i:5173 2>/dev/null || true)
if [ -n "$FRONTEND_PIDS" ]; then
    kill $FRONTEND_PIDS 2>/dev/null || true
    sleep 2
    # 强制杀死仍在运行的进程
    FRONTEND_PIDS=$(lsof -t -i:5173 2>/dev/null || true)
    if [ -n "$FRONTEND_PIDS" ]; then
        kill -9 $FRONTEND_PIDS 2>/dev/null || true
    fi
    echo -e "${GREEN}   ✅ 前端服务已停止${NC}"
else
    echo -e "${YELLOW}   ℹ️  前端服务未运行${NC}"
fi

echo ""
echo -e "${GREEN}✅ 所有服务已停止${NC}"
echo -e "${BLUE}=====================================${NC}"
