#!/bin/bash

# RAG 系统监控栈启动脚本

set -e

echo "========================================="
echo "  RAG 系统监控栈启动脚本"
echo "========================================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装,请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装,请先安装 Docker Compose"
    exit 1
fi

echo "✅ Docker 和 Docker Compose 已安装"
echo ""

# 检查 RAG 应用是否运行
if ! curl -s http://localhost:8800/health > /dev/null 2>&1; then
    echo "⚠️  警告: RAG 应用未运行或健康检查失败"
    echo "   请确保 RAG 应用在 localhost:8800 运行"
    echo ""
fi

# 启动监控栈
echo "🚀 启动监控栈..."
docker-compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker-compose ps

echo ""
echo "========================================="
echo "  监控栈启动成功!"
echo "========================================="
echo ""
echo "访问地址:"
echo "  - Grafana:      http://localhost:3000"
echo "    用户名: admin"
echo "    密码:   admin (首次登录后需修改)"
echo ""
echo "  - Prometheus:   http://localhost:9090"
echo "  - Alertmanager: http://localhost:9093"
echo ""
echo "查看日志:"
echo "  docker-compose logs -f [service_name]"
echo ""
echo "停止服务:"
echo "  docker-compose down"
echo ""
echo "========================================="
