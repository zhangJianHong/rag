#!/bin/bash

# RAG 系统快速启动脚本

echo "=== RAG 智能问答系统快速启动 ==="

# 检查必要的依赖
echo "检查依赖..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python 3.10+"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js，请先安装 Node.js 16+"
    exit 1
fi

# 检查 PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "警告: 未找到 PostgreSQL，请确保已安装并配置好 PostgreSQL + pgvector"
fi

# 设置后端
echo "设置后端环境..."
cd backend

# 创建虚拟环境（如果不存在）
# if [ ! -d "venv" ]; then
#     echo "创建 Python 虚拟环境..."
#     python3 -m venv venv
# fi

# # 激活虚拟环境
# echo "激活虚拟环境..."
# source venv/bin/activate

# 安装依赖
echo "安装后端依赖..."
pip install -r requirements.txt

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "创建环境变量文件..."
    cp .env.example .env
    echo "请编辑 backend/.env 文件，填入您的 OpenAI API 密钥和数据库连接信息"
    echo "然后重新运行此脚本"
    exit 1
fi

# 初始化数据库
echo "初始化数据库..."
python database.py

# 启动后端服务
echo "启动后端服务..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8800 &
BACKEND_PID=$!

# 设置前端
echo "设置前端环境..."
cd ../frontend

# 安装依赖
echo "安装前端依赖..."
npm install

# 启动前端服务
echo "启动前端服务..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== 系统启动完成 ==="
echo "后端服务: http://localhost:8000"
echo "前端服务: http://localhost:3000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap 'echo "正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID; exit 0' INT
wait