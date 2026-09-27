# 运维文档数据库同步工具

## 快速开始

### 方法一：使用交互式Shell脚本（推荐）

```bash
cd /home/kylin/桌面/vue-fastapi-admin-main
./sync_blog_docs.sh
```

脚本会引导您完成以下步骤：
1. 从生产服务器下载数据库
2. 预览将要同步的内容（dry-run）
3. 确认并执行实际同步
4. 备份生产数据库
5. 上传合并后的数据库
6. 切换数据库并重启服务

### 方法二：直接使用Python脚本

#### 1. 预览模式（不修改数据）

```bash
python3 vue-fastapi-admin-backend/tools/sync_blog_db.py \
  --source vue-fastapi-admin-backend/db.sqlite3 \
  --target /tmp/prod_backup.db \
  --dry-run
```

#### 2. 实际同步

```bash
python3 vue-fastapi-admin-backend/tools/sync_blog_db.py \
  --source vue-fastapi-admin-backend/db.sqlite3 \
  --target /tmp/prod_backup.db
```

## 完整工作流程

### 步骤1：从生产环境下载数据库

```bash
scp -C root@32.15.80.145:/home/data/fastapi-vue/vue-fastapi-admin-backend/db.sqlite3 ./db_prod_backup.sqlite3
```

### 步骤2：执行同步预览

```bash
python3 vue-fastapi-admin-backend/tools/sync_blog_db.py \
  --source vue-fastapi-admin-backend/db.sqlite3 \
  --target db_prod_backup.sqlite3 \
  --dry-run
```

检查输出，确认：
- 新增的分类是否符合预期
- 新增的标签是否符合预期
- 新增的文章标题是否正确
- 是否有重复标题被跳过

### 步骤3：执行实际同步

```bash
python3 vue-fastapi-admin-backend/tools/sync_blog_db.py \
  --source vue-fastapi-admin-backend/db.sqlite3 \
  --target db_prod_backup.sqlite3
```

### 步骤4：验证同步结果

```bash
sqlite3 db_prod_backup.sqlite3 <<EOF
SELECT '已发布文章数: ' || COUNT(*) FROM blog_article WHERE status='published';
SELECT '最新文章:' FROM blog_article WHERE status='published' ORDER BY created_at DESC LIMIT 3;
EOF
```

### 步骤5：上传到生产环境

```bash
# 备份生产数据库
ssh root@32.15.80.145 "cd /home/data/fastapi-vue && \
  cp vue-fastapi-admin-backend/db.sqlite3 vue-fastapi-admin-backend/db.sqlite3.bak.$(date +%Y%m%d_%H%M%S)"

# 上传新数据库
scp -C db_prod_backup.sqlite3 root@32.15.80.145:/home/data/fastapi-vue/vue-fastapi-admin-backend/db.sqlite3.new

# 切换数据库
ssh root@32.15.80.145 "cd /home/data/fastapi-vue/vue-fastapi-admin-backend && \
  mv db.sqlite3 db.sqlite3.old && \
  mv db.sqlite3.new db.sqlite3 && \
  systemctl restart vue-fastapi-backend"
```

## 功能特性

### ✅ 智能去重
- **分类**：按名称（name字段）判断唯一性
- **标签**：按名称（name字段）判断唯一性
- **文章**：按标题（title字段）判断唯一性（不区分大小写）

### ✅ 作者验证与映射
- 通过username匹配作者
- 如果作者不存在，自动使用管理员账号
- 记录所有作者映射关系

### ✅ 时间戳更新
- 同步的文章使用当前时间作为created_at和updated_at
- 避免时间混乱，便于审计追溯

### ✅ 统计字段重置
- view_count（阅读数）重置为0
- like_count（点赞数）重置为0
- is_top和is_recommend保留原值

### ✅ 事务保护
- 所有操作在事务中执行
- 失败时自动回滚
- 保证数据一致性

### ✅ Dry-run预览
- 预览将要同步的内容
- 不实际修改数据库
- 便于确认同步范围

## 命令行参数

```
usage: sync_blog_db.py [-h] --source SOURCE --target TARGET [--dry-run]

optional arguments:
  -h, --help            show this help message and exit
  --source, -s          源数据库路径（开发环境）
  --target, -t          目标数据库路径（生产环境备份）
  --dry-run, -d         预览模式，不实际写入数据
```

## 注意事项

### 数据安全
1. **始终先备份**：同步前必须备份生产数据库
2. **测试环境验证**：先在测试环境完整演练
3. **选择低峰期**：在生产环境访问量低时执行同步
4. **保留历史备份**：至少保留3个版本的数据库备份

### 同步顺序
脚本按照以下顺序同步，确保外键约束：
1. blog_category（分类表）
2. blog_tag（标签表）
3. blog_article（文章表）
4. blog_article_tag（文章标签关联表）

### 性能考虑
- 使用`scp -C`启用压缩传输
- 813MB数据库预计传输时间2-5分钟
- 建议使用有线网络连接

## 常见问题

### Q: 同步后文章的阅读数和点赞数为什么是0？
A: 这是预期行为。同步时会将统计字段重置为0，因为生产环境需要从零开始统计。

### Q: 如果作者不存在会发生什么？
A: 系统会自动将文章的author_id设置为管理员用户ID（通常是ID=1），并在日志中记录。

### Q: 可以只同步部分文章吗？
A: 当前版本会同步所有已发布的新文章。如需选择性同步，可以先在开发环境中临时修改文章状态。

### Q: 同步失败怎么办？
A: 脚本使用事务保护，失败时会自动回滚。检查错误日志，修复问题后重新执行。

## 技术实现

- **语言**: Python 3
- **数据库**: SQLite3
- **依赖**: 仅使用Python标准库（sqlite3, argparse, datetime）
- **无需安装额外依赖**

## 文件结构

```
vue-fastapi-admin-backend/
├── tools/
│   ├── __init__.py
│   └── sync_blog_db.py      # 核心同步脚本
└── db.sqlite3                # 开发环境数据库

sync_blog_docs.sh             # Shell封装脚本（项目根目录）
```

## 未来改进

- [ ] 支持MySQL数据库
- [ ] 添加增量同步功能
- [ ] 支持选择性同步（按分类、按日期等）
- [ ] 添加Web管理界面
- [ ] 自动定时同步
