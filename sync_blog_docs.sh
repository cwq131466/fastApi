#!/bin/bash
# ============================================
# 运维文档数据库同步脚本
# 功能：将开发环境已发布的文章同步到生产环境
# ============================================

set -e  # 遇到错误立即退出

# ==================== 配置区域 ====================
PROD_SERVER="32.15.80.145"                    # 生产服务器IP
PROD_USER="root"                              # 生产服务器用户
PROD_DB_PATH="/home/data/fastapi-vue/vue-fastapi-admin-backend/db.sqlite3"  # 生产数据库路径
PROJECT_ROOT="/home/kylin/桌面/vue-fastapi-admin-main"  # 项目根目录
DEV_DB_PATH="$PROJECT_ROOT/vue-fastapi-admin-backend/db.sqlite3"  # 开发数据库路径
WORK_DIR="/tmp/db_sync_workdir"               # 临时工作目录
SYNC_SCRIPT="$PROJECT_ROOT/vue-fastapi-admin-backend/tools/sync_blog_db.py"  # 同步脚本路径

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 函数定义 ====================

print_header() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  $1${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

cleanup() {
    echo ""
    print_step "清理临时文件..."
    if [ -d "$WORK_DIR" ]; then
        rm -rf "$WORK_DIR"
        print_success "临时目录已清理"
    fi
}

# 捕获中断信号
trap cleanup EXIT INT TERM

# ==================== 主流程 ====================

print_header "🚀 运维文档数据库同步工具"

# 步骤1：检查前置条件
print_step "检查前置条件..."

# 检查开发数据库是否存在
if [ ! -f "$DEV_DB_PATH" ]; then
    print_error "开发数据库不存在: $DEV_DB_PATH"
    exit 1
fi
print_success "开发数据库存在 ($(ls -lh "$DEV_DB_PATH" | awk '{print $5}'))"

# 检查同步脚本是否存在
if [ ! -f "$SYNC_SCRIPT" ]; then
    print_error "同步脚本不存在: $SYNC_SCRIPT"
    exit 1
fi
print_success "同步脚本存在"

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    print_error "未找到 Python3"
    exit 1
fi
print_success "Python3 可用 ($(python3 --version))"

echo ""

# 步骤2：选择操作模式
echo -e "${YELLOW}请选择操作模式:${NC}"
echo "  1) 完整流程（下载→同步→上传）"
echo "  2) 仅预览（dry-run，不修改数据）"
echo "  3) 仅同步本地副本（手动准备数据库）"
read -p "请输入选项 (1/2/3) [默认: 1]: " mode_choice
mode_choice=${mode_choice:-1}

echo ""

# 步骤3：根据模式执行
case $mode_choice in
    1)
        # ===== 完整流程 =====
        print_header "🔄 完整同步流程"

        # 创建临时工作目录
        mkdir -p "$WORK_DIR"
        cd "$WORK_DIR"

        # 3.1 从生产服务器下载数据库
        print_step "从生产服务器下载数据库..."
        if scp -C "${PROD_USER}@${PROD_SERVER}:${PROD_DB_PATH}" ./db_prod.sqlite3; then
            print_success "数据库下载完成"
            ls -lh db_prod.sqlite3
        else
            print_error "下载失败，请检查："
            echo "  1. 网络连接是否正常"
            echo "  2. SSH免密登录是否配置"
            echo "  3. 生产服务器路径是否正确"
            exit 1
        fi
        echo ""

        # 3.2 执行预览
        print_step "执行同步预览（dry-run）..."
        cd "$PROJECT_ROOT"
        python3 "$SYNC_SCRIPT" \
            --source "$DEV_DB_PATH" \
            --target "$WORK_DIR/db_prod.sqlite3" \
            --dry-run

        echo ""
        read -p "预览完成，是否执行实际同步？(y/n) " confirm_sync
        if [[ ! $confirm_sync =~ ^[Yy]$ ]]; then
            print_warning "已取消同步"
            exit 0
        fi
        echo ""

        # 3.3 执行实际同步
        print_step "执行实际同步..."
        python3 "$SYNC_SCRIPT" \
            --source "$DEV_DB_PATH" \
            --target "$WORK_DIR/db_prod.sqlite3"

        print_success "本地同步完成"
        echo ""

        # 3.4 备份生产数据库
        print_step "在生产服务器上创建备份..."
        BACKUP_NAME="db.sqlite3.bak.$(date +%Y%m%d_%H%M%S)"
        ssh "${PROD_USER}@${PROD_SERVER}" "cd $(dirname "$PROD_DB_PATH") && cp db.sqlite3 $BACKUP_NAME"
        print_success "备份已创建: $BACKUP_NAME"
        echo ""

        # 3.5 上传新数据库
        print_step "上传合并后的数据库到生产服务器..."
        scp -C "$WORK_DIR/db_prod.sqlite3" "${PROD_USER}@${PROD_SERVER}:${PROD_DB_PATH}.new"
        print_success "上传完成"
        echo ""

        # 3.6 切换数据库
        print_step "在生产服务器上切换数据库..."
        read -p "确认切换数据库？这将重启后端服务！(y/n) " confirm_switch
        if [[ $confirm_switch =~ ^[Yy]$ ]]; then
            ssh "${PROD_USER}@${PROD_SERVER}" "cd $(dirname "$PROD_DB_PATH") && \
                mv db.sqlite3 db.sqlite3.old && \
                mv db.sqlite3.new db.sqlite3 && \
                systemctl restart vue-fastapi-backend"

            print_success "数据库已切换，后端服务已重启"
        else
            print_warning "数据库未切换，新文件位于: ${PROD_DB_PATH}.new"
            echo "要手动切换，请在生产服务器执行:"
            echo "  cd $(dirname "$PROD_DB_PATH")"
            echo "  mv db.sqlite3 db.sqlite3.old"
            echo "  mv db.sqlite3.new db.sqlite3"
            echo "  systemctl restart vue-fastapi-backend"
        fi
        ;;

    2)
        # ===== 仅预览 =====
        print_header "👁️  预览模式"

        # 需要用户提供目标数据库
        read -p "请输入目标数据库路径: " target_db

        if [ ! -f "$target_db" ]; then
            print_error "目标数据库不存在: $target_db"
            exit 1
        fi

        python3 "$SYNC_SCRIPT" \
            --source "$DEV_DB_PATH" \
            --target "$target_db" \
            --dry-run
        ;;

    3)
        # ===== 仅同步本地副本 =====
        print_header "🔧 本地同步模式"

        read -p "请输入源数据库路径 [默认: $DEV_DB_PATH]: " source_db
        source_db=${source_db:-$DEV_DB_PATH}

        read -p "请输入目标数据库路径: " target_db

        if [ ! -f "$source_db" ]; then
            print_error "源数据库不存在: $source_db"
            exit 1
        fi

        if [ ! -f "$target_db" ]; then
            print_error "目标数据库不存在: $target_db"
            exit 1
        fi

        # 先预览
        print_step "预览模式..."
        python3 "$SYNC_SCRIPT" \
            --source "$source_db" \
            --target "$target_db" \
            --dry-run

        echo ""
        read -p "是否执行实际同步？(y/n) " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            python3 "$SYNC_SCRIPT" \
                --source "$source_db" \
                --target "$target_db"
            print_success "同步完成"
        else
            print_warning "已取消"
        fi
        ;;

    *)
        print_error "无效选项"
        exit 1
        ;;
esac

echo ""
print_header "✨ 同步流程结束"
echo -e "${GREEN}提示:${NC}"
echo "  - 访问生产环境验证: http://32.15.80.145"
echo "  - API文档: http://32.15.80.145:9090/docs"
echo "  - 查看同步日志: logs/sync_$(date +%Y%m%d).log"
echo ""
