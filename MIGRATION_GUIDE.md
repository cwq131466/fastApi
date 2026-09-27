# SQLite 到 MySQL 数据库迁移指南

本指南将帮助你从 SQLite 数据库迁移到 MySQL 数据库,适用于生产环境部署。

## 目录

- [前置要求](#前置要求)
- [迁移步骤](#迁移步骤)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 前置要求

### 1. 安装 MySQL 服务器

确保你的生产环境已安装 MySQL 或 MariaDB:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server

# 或者使用 Docker
docker run --name mysql -e MYSQL_ROOT_PASSWORD=your_password -p 3306:3306 -d mysql:8.0
```

### 2. 创建 MySQL 数据库和用户

```sql
-- 登录 MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE vue_fastapi_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户(推荐)
CREATE USER 'vue_admin'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON vue_fastapi_admin.* TO 'vue_admin'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 安装 Python 依赖

```bash
cd vue-fastapi-admin-backend

# 激活虚拟环境(如果使用)
source env/bin/activate  # Linux/Mac
# 或
env\Scripts\activate     # Windows

# 安装新依赖
pip install pandas sqlalchemy pymysql

# 更新 requirements.txt 中的依赖
pip install -r requirements.txt
```

---

## 迁移步骤

### 步骤 1: 备份现有数据

```bash
# 备份 SQLite 数据库文件
cp vue-fastapi-admin-backend/db.sqlite3 vue-fastapi-admin-backend/db.sqlite3.backup

# 如果已有 MySQL 数据,也进行备份
mysqldump -u root -p vue_fastapi_admin > backup_$(date +%Y%m%d).sql
```

### 步骤 2: 配置环境变量

编辑 `vue-fastapi-admin-backend/.env` 文件:

```bash
# 修改数据库类型为 mysql
DB_TYPE=mysql

# 配置 MySQL 连接参数
DB_HOST=localhost          # MySQL 服务器地址
DB_PORT=3306              # MySQL 端口
DB_USER=root              # MySQL 用户名(建议使用专用用户)
DB_PASSWORD=your_password # MySQL 密码
DB_NAME=vue_fastapi_admin # 数据库名称
```

**安全提示**: 生产环境中不要将密码硬编码在 `.env` 文件中,建议使用环境变量或密钥管理服务。

### 步骤 3: 运行迁移脚本

```bash
cd vue-fastapi-admin-backend

# 运行迁移脚本
python migrate_sqlite_to_mysql.py
```

脚本会:
1. 检测 SQLite 数据库中的所有表
2. 自动创建 MySQL 数据库(如果不存在)
3. 逐表迁移数据
4. 显示迁移进度和结果

### 步骤 4: 验证迁移结果

```bash
# 登录 MySQL 检查数据
mysql -u root -p

USE vue_fastapi_admin;
SHOW TABLES;
SELECT COUNT(*) FROM sys_user;  # 检查用户表数据
```

### 步骤 5: 初始化 Aerich 迁移系统

由于切换到 MySQL,需要重新初始化 Aerich 迁移历史:

```bash
cd vue-fastapi-admin-backend

# 删除旧的迁移历史(如果需要保留请备份)
rm -rf migrations/models/*.py

# 初始化新的迁移
aerich init -t app.settings.TORTOISE_ORM

# 生成初始迁移文件
aerich init-db

# 应用迁移(创建表结构)
aerich upgrade
```

### 步骤 6: 启动应用测试

```bash
# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 9099

# 检查日志确认数据库连接正常
```

访问应用并测试基本功能:
- 用户登录
- 数据查询
- 数据创建/更新/删除

---

## 配置说明

### 开发环境 (使用 SQLite)

`.env`:
```bash
DB_TYPE=sqlite
```

### 生产环境 (使用 MySQL)

`.env`:
```bash
DB_TYPE=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=vue_admin
DB_PASSWORD=secure_password_here
DB_NAME=vue_fastapi_admin
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| DB_TYPE | 数据库类型 (sqlite/mysql) | sqlite |
| DB_HOST | MySQL 服务器地址 | localhost |
| DB_PORT | MySQL 端口 | 3306 |
| DB_USER | MySQL 用户名 | root |
| DB_PASSWORD | MySQL 密码 | (空) |
| DB_NAME | 数据库名称 | vue_fastapi_admin |

---

## 常见问题

### Q1: 迁移时出现 "Access denied" 错误

**解决方案**:
```sql
-- 检查用户权限
SELECT user, host FROM mysql.user;

-- 授予权限
GRANT ALL PRIVILEGES ON vue_fastapi_admin.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

### Q2: 中文字符显示为乱码

**解决方案**:
确保数据库使用 utf8mb4 字符集:
```sql
ALTER DATABASE vue_fastapi_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Q3: 迁移后外键约束问题

Tortoise ORM 会自动处理外键关系。如果遇到外键问题:
```bash
# 重新生成迁移文件
aerich heads
aerich upgrade
```

### Q4: 性能优化建议

对于生产环境 MySQL 配置:

1. **调整 MySQL 配置** (`/etc/mysql/my.cnf`):
```ini
[mysqld]
max_connections = 200
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
query_cache_size = 64M
```

2. **添加索引**:
```sql
-- 根据查询模式添加合适的索引
CREATE INDEX idx_user_username ON sys_user(username);
CREATE INDEX idx_role_name ON sys_role(name);
```

3. **使用连接池**:
在项目中使用 Tortoise ORM 的连接池配置。

### Q5: 如何回滚到 SQLite?

```bash
# 1. 修改 .env
DB_TYPE=sqlite

# 2. 恢复 SQLite 数据库
cp db.sqlite3.backup db.sqlite3

# 3. 重启应用
```

### Q6: 迁移脚本失败怎么办?

检查以下几点:
1. MySQL 服务是否正常运行: `systemctl status mysql`
2. 网络连接是否正常: `telnet localhost 3306`
3. 用户权限是否正确
4. 查看详细错误日志

手动迁移单个表:
```python
# 使用 Python 交互式环境
from migrate_sqlite_to_mysql import *
df = read_sqlite_data('db.sqlite3', 'sys_user')
write_mysql_data(df, mysql_url, 'sys_user')
```

---

## 后续维护

### 定期备份 MySQL

```bash
# 创建备份脚本 backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u root -p'password' vue_fastapi_admin > /backup/vue_admin_$DATE.sql
find /backup -name "vue_admin_*.sql" -mtime +30 -delete  # 保留30天
```

```bash
# 添加到 crontab (每天凌晨2点备份)
crontab -e
0 2 * * * /path/to/backup.sh
```

### 监控数据库性能

```sql
-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log%';
SET GLOBAL slow_query_log = 'ON';

-- 查看当前连接数
SHOW STATUS LIKE 'Threads_connected';

-- 查看表大小
SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'vue_fastapi_admin'
ORDER BY (data_length + index_length) DESC;
```

---

## 技术支持

如遇到问题,请检查:
1. 应用日志: `vue-fastapi-admin-backend/app/logs/`
2. MySQL 错误日志: `/var/log/mysql/error.log`
3. Python 版本兼容性: 确保使用 Python 3.8+

---

**注意**: 迁移前务必做好数据备份!
