#!/bin/bash

echo "========================================"
echo "  Vue-FastAPI-Admin 一键启动"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python3"
    exit 1
fi

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo "[错误] 未检测到 Node.js，请先安装 Node.js"
    exit 1
fi

echo "[1/4] 检查 Python 虚拟环境..."
if [ ! -d "vue-fastapi-admin-backend/env" ]; then
    echo "创建虚拟环境..."
    # 优先使用 pyenv 的 Python 3.11
    if command -v /home/kylin/.pyenv/versions/3.11.14/bin/python3 &> /dev/null; then
        /home/kylin/.pyenv/versions/3.11.14/bin/python3 -m venv vue-fastapi-admin-backend/env
    else
        python3 -m venv vue-fastapi-admin-backend/env
    fi
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败"
        exit 1
    fi
    echo "虚拟环境创建成功"
else
    echo "虚拟环境已存在"
fi
echo ""

# echo "[2/4] 安装后端依赖..."
# source vue-fastapi-admin-backend/env/bin/activate
# # 先尝试从离线包安装，缺失的再从网络安装
# pip install --no-index --find-links=./vue-fastapi-admin-backend/packages -r vue-fastapi-admin-backend/requirements.txt 2>/dev/null || true
# # 补充安装可能缺失的网络依赖
# pip install paramiko drf-httpsig requests loguru colorama itsdangerous -q
# if [ $? -ne 0 ]; then
#    echo "[错误] 安装后端依赖失败"
#    exit 1
# fi
# echo "后端依赖安装完成"
# echo ""

echo "[3/4] 检查前端依赖..."
cd web_backend
if [ ! -d "node_modules" ]; then
    echo "安装 web_backend 依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "[错误] 安装 web_backend 依赖失败"
        exit 1
    fi
else
    echo "web_backend 依赖已存在"
fi
cd ..

cd web_frontend
if [ ! -d "node_modules" ]; then
    echo "安装 web_frontend 依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "[错误] 安装 web_frontend 依赖失败"
        exit 1
    fi
else
    echo "web_frontend 依赖已存在"
fi
cd ..
echo "前端依赖检查完成"
echo ""

echo "[4/4] 启动所有服务..."
echo ""
echo "========================================"
echo "  后端服务: http://localhost:9099"
echo "  API文档:  http://localhost:9099/docs"
echo "  Web后台:  http://localhost:5173 (web_backend)"
echo "  Web前台:  http://localhost:5174 (web_frontend)"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "========================================"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo "正在停止所有服务..."
    kill $BACKEND_PID $WEB_BACKEND_PID $WEB_FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $WEB_BACKEND_PID $WEB_FRONTEND_PID 2>/dev/null
    echo "所有服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM
cd vue-fastapi-admin-backend
source env/bin/activate
# 启动后端（使用pyenv的Python 3.11）
# export PATH="/home/kylin/.pyenv/versions/3.11.14/bin:$PATH"
python run.py &
BACKEND_PID=$!

# 等待2秒让后端先启动
sleep 2
cd ..

# 启动 web_backend (管理后台)
cd web_backend
npm run dev &
WEB_BACKEND_PID=$!
cd ..

# 等待1秒
sleep 1

# 启动 web_frontend (前台)
cd web_frontend
npm run dev &
WEB_FRONTEND_PID=$!
cd ..

echo "所有服务已启动!"
echo ""

# 等待所有进程
wait $BACKEND_PID $WEB_BACKEND_PID $WEB_FRONTEND_PID
