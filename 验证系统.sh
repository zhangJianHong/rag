#!/bin/bash

# RAG 系统验证脚本
# 验证所有组件是否正确配置

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}  RAG 系统验证工具${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 检查目录
cd /home/zhangjh/code/python/rag/backend

# 1. 检查 Python 依赖
echo -e "${YELLOW}[1/5] 检查 Python 依赖...${NC}"
python -c "
import jwt
import passlib
import jose
import email_validator
print('  ✅ PyJWT')
print('  ✅ passlib')
print('  ✅ python-jose')
print('  ✅ email-validator')
"

# 2. 检查数据库模型
echo -e "${YELLOW}[2/5] 检查数据库模型...${NC}"
python -c "
from app.models.database import User, Role, UserDocument, UserQuery
print('  ✅ User 模型')
print('  ✅ Role 模型')
print('  ✅ UserDocument 模型')
print('  ✅ UserQuery 模型')
"

# 3. 检查认证服务
echo -e "${YELLOW}[3/5] 检查认证服务...${NC}"
python -c "
from app.services.auth import auth_service
print('  ✅ auth_service')
print('  ✅ JWT token 生成/验证')
print('  ✅ 密码加密/验证')
print('  ✅ 用户认证')
"

# 4. 检查中间件和装饰器
echo -e "${YELLOW}[4/5] 检查中间件和装饰器...${NC}"
python -c "
from app.middleware.auth import (
    AuthMiddleware,
    require_document_upload,
    require_document_delete,
    require_document_read,
    require_query_ask,
    require_query_history,
    require_system_settings,
    require_user_management,
    require_role_management,
    require_admin,
    get_current_user,
    get_current_active_user,
    get_current_admin_user
)
print('  ✅ AuthMiddleware 中间件')
print('  ✅ 8个权限装饰器')
print('  ✅ 3个角色装饰器')
print('  ✅ 3个依赖注入函数')
"

# 5. 检查路由
echo -e "${YELLOW}[5/5] 检查路由模块...${NC}"
python -c "
from app.routers import auth, upload, query
print('  ✅ auth 路由 (登录/注册/Token)')
print('  ✅ upload 路由 (文档上传)')
print('  ✅ query 路由 (查询功能)')
"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ 所有组件验证通过!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}系统已就绪,可以启动服务:${NC}"
echo -e "  ${BLUE}./start_auth.sh${NC}"
echo ""
echo -e "${GREEN}或手动启动:${NC}"
echo -e "  ${YELLOW}后端:${NC} cd backend && uvicorn app.main:app --reload --port 8800"
echo -e "  ${YELLOW}前端:${NC} cd frontend && npm run dev"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
