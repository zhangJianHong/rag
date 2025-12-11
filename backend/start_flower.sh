#!/bin/bash
# Flower 监控启动脚本 (Celery任务监控工具)

echo "==============================================="
echo "启动 Flower - Celery 监控界面"
echo "==============================================="

# 进入项目目录
cd "$(dirname "$0")"

# 激活虚拟环境
source ../venv/bin/activate

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动Flower
celery -A app.celery_app flower \
  --port=5555 \
  --broker_api=http://localhost:6379/0

echo "Flower 监控界面: http://localhost:5555"
echo "Flower 已停止"
