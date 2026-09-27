#!/bin/bash

# 前端部署脚本
echo "开始部署前端文件..."

# 源目录和目标目录
SRC_DIR="/home/kylin/桌面/vue-fastapi-admin-main/web_backend/dist"
DEST_DIR="/var/www/vue-admin/web"

# 检查源目录是否存在
if [ ! -d "$SRC_DIR" ]; then
    echo "错误: 源目录 $SRC_DIR 不存在"
    exit 1
fi

# 清空目标目录
echo "清空目标目录..."
sudo rm -rf ${DEST_DIR:?}/*

# 复制文件
echo "复制文件到 $DEST_DIR ..."
sudo cp -r "$SRC_DIR"/* "$DEST_DIR"/

# 设置权限
echo "设置文件权限..."
sudo chown -R www-data:www-data "$DEST_DIR"
sudo chmod -R 755 "$DEST_DIR"

# 验证部署
echo ""
echo "部署完成！验证文件结构："
ls -la "$DEST_DIR"
echo ""
echo "Assets 目录："
ls -la "$DEST_DIR/assets"
echo ""
echo "Resource 目录："
ls -la "$DEST_DIR/resource" 2>/dev/null || echo "resource 目录不存在"

echo ""
echo "重启 Nginx 以使更改生效："
sudo systemctl restart nginx

echo ""
echo "部署成功！"
