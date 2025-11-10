#!/bin/bash

# RAG 智能问答系统 - 认证系统启动脚本
# 功能: 初始化并启动包含认证功能的完整系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/home/zhangjh/code/python/rag"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}RAG 智能问答系统 - 启动程序${NC}"
echo -e "${BLUE}(包含用户认证与权限管理)${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# 函数: 检查数据库是否已初始化
check_db_initialized() {
    echo -e "${YELLOW}[1/5] 检查数据库状态...${NC}"
    cd "$BACKEND_DIR"

    # 检查是否存在 users 表
    RESULT=$(python -c "
from sqlalchemy import create_engine, inspect
from app.config import settings
try:
    engine = create_engine(settings.DB_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print('users' in tables)
except:
    print('False')
" 2>/dev/null)

    if [ "$RESULT" != "True" ]; then
        echo -e "${YELLOW}   数据库未初始化,开始初始化...${NC}"
        python -m app.migrations.init_auth
        echo -e "${GREEN}   ✅ 数据库初始化完成${NC}"
    else
        echo -e "${GREEN}   ✅ 数据库已初始化${NC}"
    fi
}

# 函数: 检查后端依赖
check_backend_deps() {
    echo -e "${YELLOW}[2/5] 检查后端依赖...${NC}"
    cd "$BACKEND_DIR"

    # 检查关键依赖是否已安装
    python -c "import jwt; import passlib; import jose; import email_validator" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}   安装后端依赖...${NC}"
        pip install -q -r requirements.txt
        echo -e "${GREEN}   ✅ 后端依赖安装完成${NC}"
    else
        echo -e "${GREEN}   ✅ 后端依赖已安装${NC}"
    fi
}

# 函数: 检查前端依赖
check_frontend_deps() {
    echo -e "${YELLOW}[3/5] 检查前端依赖...${NC}"
    cd "$FRONTEND_DIR"

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}   安装前端依赖...${NC}"
        npm install
        echo -e "${GREEN}   ✅ 前端依赖安装完成${NC}"
    else
        echo -e "${GREEN}   ✅ 前端依赖已安装${NC}"
    fi
}

# 函数: 启动后端服务
start_backend() {
    echo -e "${YELLOW}[4/5] 启动后端服务...${NC}"
    cd "$BACKEND_DIR"

    # 检查端口 8800 是否被占用
    if lsof -Pi :8800 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}   端口 8800 已被占用,尝试停止旧进程...${NC}"
        kill $(lsof -t -i:8800) 2>/dev/null || true
        sleep 2
    fi

    # 启动后端
    nohup uvicorn app.main:app --reload --port 8800 --host 0.0.0.0 > /tmp/rag_backend.log 2>&1 &
    BACKEND_PID=$!

    # 等待后端启动
    echo -e "${YELLOW}   等待后端启动...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8800/docs > /dev/null 2>&1; then
            echo -e "${GREEN}   ✅ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
            echo -e "${GREEN}   📝 API文档: http://localhost:8800/docs${NC}"
            return 0
        fi
        sleep 1
    done

    echo -e "${RED}   ❌ 后端启动失败,请查看日志: /tmp/rag_backend.log${NC}"
    return 1
}

# 函数: 启动前端服务
start_frontend() {
    echo -e "${YELLOW}[5/5] 启动前端服务...${NC}"
    cd "$FRONTEND_DIR"

    # 检查端口 5173 是否被占用
    if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}   端口 5173 已被占用,尝试停止旧进程...${NC}"
        kill $(lsof -t -i:5173) 2>/dev/null || true
        sleep 2
    fi

    # 启动前端
    nohup npm run dev > /tmp/rag_frontend.log 2>&1 &
    FRONTEND_PID=$!

    # 等待前端启动
    echo -e "${YELLOW}   等待前端启动...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            echo -e "${GREEN}   ✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
            echo -e "${GREEN}   🌐 访问地址: http://localhost:5173${NC}"
            return 0
        fi
        sleep 1
    done

    echo -e "${RED}   ❌ 前端启动失败,请查看日志: /tmp/rag_frontend.log${NC}"
    return 1
}

# 主流程
main() {
    # 检查并初始化数据库
    check_db_initialized

    # 检查依赖
    check_backend_deps
    check_frontend_deps

    # 启动服务
    start_backend
    if [ $? -ne 0 ]; then
        exit 1
    fi

    start_frontend
    if [ $? -ne 0 ]; then
        exit 1
    fi

    echo ""
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${GREEN}✅ 系统启动成功!${NC}"
    echo -e "${BLUE}=====================================${NC}"
    echo ""
    echo -e "${GREEN}📌 服务信息:${NC}"
    echo -e "   后端 API: ${BLUE}http://localhost:8800${NC}"
    echo -e "   API 文档: ${BLUE}http://localhost:8800/docs${NC}"
    echo -e "   前端应用: ${BLUE}http://localhost:5173${NC}"
    echo ""
    echo -e "${GREEN}📌 默认管理员账号:${NC}"
    echo -e "   用户名: ${YELLOW}admin${NC}"
    echo -e "   密码: ${YELLOW}admin123${NC}"
    echo -e "   ${RED}⚠️  请登录后立即修改密码!${NC}"
    echo ""
    echo -e "${GREEN}📌 功能特性:${NC}"
    echo -e "   ✅ 用户登录/注册/密码管理"
    echo -e "   ✅ 三级角色权限 (管理员/普通用户/只读用户)"
    echo -e "   ✅ 细粒度权限控制"
    echo -e "   ✅ 科技风格UI设计"
    echo -e "   ✅ JWT令牌认证"
    echo -e "   ✅ 数据隔离保护"
    echo ""
    echo -e "${GREEN}📌 日志文件:${NC}"
    echo -e "   后端日志: ${BLUE}/tmp/rag_backend.log${NC}"
    echo -e "   前端日志: ${BLUE}/tmp/rag_frontend.log${NC}"
    echo ""
    echo -e "${YELLOW}💡 查看使用说明: cat 认证系统使用说明.md${NC}"
    echo -e "${YELLOW}💡 停止服务请运行: ./stop.sh${NC}"
    echo -e "${BLUE}=====================================${NC}"
}

# 执行主流程
main
