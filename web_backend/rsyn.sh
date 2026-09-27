#!/bin/bash
# scripts/sync_to_prod.sh
# 同步代码到内网生产环境

set -e  # 遇到错误立即退出

# ==================== 配置区域 ====================
PROD_SERVER="32.15.80.145"          # 生产服务器IP
PROD_USER="root"                    # 生产服务器用户
PROD_PATH="/home/data/fastapi-vue"  # 生产环境路径
LOCAL_PATH="/home/kylin/桌面/vue-fastapi-admin-main"  # 项目根目录

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  🚀 开始同步代码到生产环境${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# ==================== 前置检查 ====================
echo -e "${YELLOW}📋 前置检查...${NC}"

# 检查是否有未提交的更改
if ! git diff --quiet 2>/dev/null; then
    echo -e "${RED}⚠️  警告：有未提交的 Git 更改${NC}"
    read -p "是否继续同步？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ 已取消${NC}"
        exit 1
    fi
fi

# 测试 SSH 连接
echo -e "🔌 测试 SSH 连接..."
if ! ssh -o ConnectTimeout=5 "${PROD_USER}@${PROD_SERVER}" "echo '连接成功'" > /dev/null 2>&1; then
    echo -e "${RED}❌ 无法连接到生产服务器: ${PROD_SERVER}${NC}"
    echo "请检查："
    echo "  1. 网络是否通畅"
    echo "  2. SSH 服务是否运行"
    echo "  3. 是否配置了免密登录"
    exit 1
fi
echo -e "${GREEN}✅ SSH 连接正常${NC}"
echo ""

# ==================== 构建前端 ====================
echo -e "${YELLOW}📦 构建前端项目...${NC}"

# 构建 web_backend (Naive UI)
echo -e "  🎨 构建 web_backend (Naive UI)..."
cd "$LOCAL_PATH/web_backend"
if [ ! -d "node_modules" ]; then
    echo "    安装依赖..."
    npm install
fi
npm run build
echo -e "  ${GREEN}✅ web_backend 构建完成${NC}"

# 构建 web_frontend (Element Plus)
echo -e "  🎨 构建 web_frontend (Element Plus)..."
cd "$LOCAL_PATH/web_frontend"
if [ ! -d "node_modules" ]; then
    echo "    安装依赖..."
    npm install
fi
npm run build
echo -e "  ${GREEN}✅ web_frontend 构建完成${NC}"

cd "$LOCAL_PATH"
echo ""

# ==================== 同步代码 ====================
echo -e "${YELLOW}📤 同步代码...${NC}"

rsync -avz  \
    --exclude='.git' \
    --exclude='.gitignore' \
    --exclude='vue-fastapi-admin-backend/env' \
    --exclude='vue-fastapi-admin-backend/uploads/*' \
    --exclude='.lingma' \
    --exclude='packages' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='start.sh' \
    --exclude='rsyn.sh' \
    --exclude='.pytest_cache' \
    --exclude='.mypy_cache' \
    --exclude='node_modules' \
    --exclude='deploy/' \
    --exclude='.env' \
    --exclude='db.sqlite3-*' \
    --exclude='db.sqlite3' \
    --exclude='uploads/' \
    "$LOCAL_PATH/" \
    "${PROD_USER}@${PROD_SERVER}:${PROD_PATH}/"

echo -e "${GREEN}✅ 代码同步完成${NC}"
echo ""

