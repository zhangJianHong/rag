#!/bin/bash

# RAG 应用部署脚本
# 使用方法: ./deploy.sh [environment]
# environment: dev (默认) | prod

set -e

ENVIRONMENT=${1:-dev}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo "🚀 部署到生产环境..."
else
    echo "🔧 部署到开发环境..."
fi

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    echo "❌ 错误: .env 文件不存在，请从 .env.example 复制并配置"
    exit 1
fi

# 检查 docker-compose 文件是否存在
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ 错误: $COMPOSE_FILE 文件不存在"
    exit 1
fi

echo "📋 使用配置文件: $COMPOSE_FILE"

# 停止现有服务
echo "⏹️  停止现有服务..."
docker-compose -f "$COMPOSE_FILE" down

# 清理未使用的镜像 (仅生产环境)
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "🧹 清理未使用的镜像..."
    docker image prune -f
fi

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose -f "$COMPOSE_FILE" up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose -f "$COMPOSE_FILE" ps

# 显示服务日志
echo "📝 显示最近的日志..."
docker-compose -f "$COMPOSE_FILE" logs --tail=20

echo "✅ 部署完成!"
echo ""
echo "🌐 访问地址:"
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "   前端: http://localhost"
    echo "   后端: http://localhost:8800"
else
    echo "   前端: http://localhost:3000"
    echo "   后端: http://localhost:8800"
fi
echo "   数据库: localhost:5432"
echo ""
echo "🔍 查看实时日志: docker-compose -f $COMPOSE_FILE logs -f"
echo "🛑 停止服务: docker-compose -f $COMPOSE_FILE down"