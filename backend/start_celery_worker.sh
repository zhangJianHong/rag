#!/bin/bash
# Celery Worker 启动脚本

echo "==============================================="
echo "启动 Celery Worker"
echo "==============================================="

# 进入项目目录
cd "$(dirname "$0")"

# 激活虚拟环境
source ../venv/bin/activate

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动Celery Worker
celery -A app.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000 \
  --time-limit=1800 \
  --soft-time-limit=1500 \
  -Q indexing \
  -n worker@%h

echo "Celery Worker 已停止"
