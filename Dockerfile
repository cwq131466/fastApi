# ============================================
# Multi-stage Dockerfile for Vue-FastAPI-Admin
# ============================================
# Stage 1: Build web_backend (Naive UI Admin)
# ============================================
FROM node:18-alpine AS web_backend_builder

WORKDIR /build/web_backend
COPY web_backend/package*.json ./
RUN npm ci --registry=https://registry.npmmirror.com
COPY web_backend/ ./
RUN npm run build

# ============================================
# Stage 2: Build web_frontend (Element Plus)
# ============================================
FROM node:18-alpine AS web_frontend_builder

WORKDIR /build/web_frontend
COPY web_frontend/package*.json ./
RUN npm ci --registry=https://registry.npmmirror.com
COPY web_frontend/ ./
RUN npm run build

# ============================================
# Stage 3: Python backend + Nginx
# ============================================
FROM python:3.11-slim-bullseye

# Set working directory
WORKDIR /opt/vue-fastapi-admin

# Install system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=core-apt \
    --mount=type=cache,target=/var/lib/apt,sharing=locked,id=core-apt \
    sed -i "s@http://.*.debian.org@http://mirrors.ustc.edu.cn@g" /etc/apt/sources.list \
    && rm -f /etc/apt/apt.conf.d/docker-clean \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        bash \
        nginx \
        curl \
        procps \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY vue-fastapi-admin-backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy backend code
COPY vue-fastapi-admin-backend/ ./backend/

# Copy frontend build artifacts
COPY --from=web_backend_builder /build/web_backend/dist ./web_backend/dist
COPY --from=web_frontend_builder /build/web_frontend/dist ./web_frontend/dist

# Copy Nginx configuration
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

# Create necessary directories
RUN mkdir -p /opt/vue-fastapi-admin/backend/uploads \
    /opt/vue-fastapi-admin/backend/logs \
    /opt/vue-fastapi-admin/backend/migrations

# Set environment variables
ENV LANG=zh_CN.UTF-8
ENV PYTHONPATH=/opt/vue-fastapi-admin/backend
ENV APP_ENV=production

# Expose ports
EXPOSE 80      # Nginx (frontend)
EXPOSE 9090    # FastAPI backend

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9090/api/v1/base/health || exit 1

# Start script
COPY deploy/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
