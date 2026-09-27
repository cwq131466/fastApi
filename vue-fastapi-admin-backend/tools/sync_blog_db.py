#!/usr/bin/env python3
"""
运维文档数据库同步工具

功能：
- 将开发环境中已发布的文章同步到生产环境数据库
- 智能处理分类、标签的合并（按名称去重）
- 验证作者是否存在，不存在则使用管理员账号
- 更新同步文章的时间戳为当前时间
- 支持 dry-run 预览模式

使用方法：
    python sync_blog_db.py --source dev.db --target prod.db [--dry-run]
"""

import argparse
import asyncio
import sqlite3
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional


class BlogDatabaseSyncer:
    """博客数据库同步器"""

    def __init__(self, source_db: str, target_db: str, dry_run: bool = False):
        """
        初始化同步器

        Args:
            source_db: 源数据库路径（开发环境）
            target_db: 目标数据库路径（生产环境备份）
            dry_run: 是否仅预览，不实际写入
        """
        self.source_db = source_db
        self.target_db = target_db
        self.dry_run = dry_run
        self.sync_time = datetime.now()

        # ID映射表
        self.category_id_map: Dict[int, int] = {}
        self.tag_id_map: Dict[int, int] = {}
        self.article_id_map: Dict[int, int] = {}

        # 统计信息
        self.stats = {
            'categories_added': 0,
            'tags_added': 0,
            'articles_added': 0,
            'articles_skipped': 0,
            'article_tags_added': 0,
        }

        # 详细日志
        self.logs: List[str] = []

    def log(self, message: str):
        """记录日志"""
        timestamp = self.sync_time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def get_connection(self, db_path: str) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def sync_categories(self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection):
        """同步分类表"""
        self.log("\n📁 开始同步分类...")

        # 获取源库中所有激活的分类
        source_categories = source_conn.execute(
            "SELECT * FROM blog_category WHERE is_active=1 ORDER BY id"
        ).fetchall()

        # 获取目标库中已有的分类名称集合
        target_category_names = set()
        for row in target_conn.execute("SELECT id, name FROM blog_category"):
            target_category_names.add(row['name'])

        # 找出需要新增的分类
        new_categories = []
        for cat in source_categories:
            if cat['name'] not in target_category_names:
                new_categories.append(cat)
            else:
                # 记录已存在的分类，建立ID映射
                target_row = target_conn.execute(
                    "SELECT id FROM blog_category WHERE name=?", (cat['name'],)
                ).fetchone()
                if target_row:
                    self.category_id_map[cat['id']] = target_row['id']

        self.log(f"  发现 {len(new_categories)} 个新分类")

        # 插入新分类
        for cat in new_categories:
            if self.dry_run:
                self.log(f"    [预览] 将新增分类: {cat['name']} (slug: {cat['slug']})")
            else:
                cursor = target_conn.execute(
                    """INSERT INTO blog_category
                       (name, slug, parent_id, icon, description, `order`, is_active, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        cat['name'], cat['slug'], cat['parent_id'],
                        cat['icon'], cat['description'], cat['order'],
                        cat['is_active'], self.sync_time.isoformat(), self.sync_time.isoformat()
                    )
                )
                new_id = cursor.lastrowid
                self.category_id_map[cat['id']] = new_id
                self.log(f"    ✅ 新增分类: {cat['name']} (ID: {new_id})")

            self.stats['categories_added'] += 1

    def sync_tags(self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection):
        """同步标签表"""
        self.log("\n🏷️  开始同步标签...")

        # 获取源库中所有激活的标签
        source_tags = source_conn.execute(
            "SELECT * FROM blog_tag WHERE is_active=1 ORDER BY id"
        ).fetchall()

        # 获取目标库中已有的标签名称集合
        target_tag_names = set()
        for row in target_conn.execute("SELECT id, name FROM blog_tag"):
            target_tag_names.add(row['name'])

        # 找出需要新增的标签
        new_tags = []
        for tag in source_tags:
            if tag['name'] not in target_tag_names:
                new_tags.append(tag)
            else:
                # 记录已存在的标签，建立ID映射
                target_row = target_conn.execute(
                    "SELECT id FROM blog_tag WHERE name=?", (tag['name'],)
                ).fetchone()
                if target_row:
                    self.tag_id_map[tag['id']] = target_row['id']

        self.log(f"  发现 {len(new_tags)} 个新标签")

        # 插入新标签
        for tag in new_tags:
            if self.dry_run:
                self.log(f"    [预览] 将新增标签: {tag['name']} (slug: {tag['slug']})")
            else:
                cursor = target_conn.execute(
                    """INSERT INTO blog_tag
                       (name, slug, color, article_count, is_active, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        tag['name'], tag['slug'], tag['color'],
                        0, tag['is_active'],  # article_count初始化为0
                        self.sync_time.isoformat(), self.sync_time.isoformat()
                    )
                )
                new_id = cursor.lastrowid
                self.tag_id_map[tag['id']] = new_id
                self.log(f"    ✅ 新增标签: {tag['name']} (ID: {new_id})")

            self.stats['tags_added'] += 1

    def get_or_create_admin_user(self, target_conn: sqlite3.Connection) -> int:
        """获取或创建管理员用户ID"""
        # 查找超级管理员用户
        admin = target_conn.execute(
            "SELECT id FROM user WHERE is_superuser=1 ORDER BY id LIMIT 1"
        ).fetchone()

        if admin:
            return admin['id']

        # 如果没有管理员，使用第一个用户
        first_user = target_conn.execute(
            "SELECT id FROM user ORDER BY id LIMIT 1"
        ).fetchone()

        if first_user:
            return first_user['id']

        raise Exception("目标数据库中没有任何用户，无法同步文章")

    def resolve_author_id(self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection,
                         source_author_id: int) -> int:
        """
        解析作者ID

        Args:
            source_conn: 源数据库连接
            target_conn: 目标数据库连接
            source_author_id: 源数据库中的作者ID

        Returns:
            目标数据库中对应的作者ID
        """
        # 从源库获取作者username
        source_author = source_conn.execute(
            "SELECT id, username FROM user WHERE id=?", (source_author_id,)
        ).fetchone()

        if not source_author:
            # 如果源库中找不到作者，使用管理员
            self.log(f"    ⚠️  源库中作者ID {source_author_id} 不存在，使用管理员账号")
            return self.get_or_create_admin_user(target_conn)

        # 在目标库中查找相同username的用户
        target_author = target_conn.execute(
            "SELECT id FROM user WHERE username=?", (source_author['username'],)
        ).fetchone()

        if target_author:
            self.log(f"    ✅ 找到匹配作者: {source_author['username']} (ID: {target_author['id']})")
            return target_author['id']
        else:
            # 作者不存在，使用管理员账号
            admin_id = self.get_or_create_admin_user(target_conn)
            self.log(f"    ⚠️  作者 '{source_author['username']}' 不存在，使用管理员账号 (ID: {admin_id})")
            return admin_id

    def sync_articles(self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection):
        """同步文章表"""
        self.log("\n📝 开始同步已发布文章...")

        # 获取源库中所有已发布的文章
        source_articles = source_conn.execute(
            """SELECT * FROM blog_article
               WHERE status='published'
               ORDER BY id"""
        ).fetchall()

        # 获取目标库中已有的文章标题集合
        target_article_titles = set()
        for row in target_conn.execute("SELECT id, title FROM blog_article"):
            target_article_titles.add(row['title'].lower())  # 不区分大小写

        self.log(f"  源库中有 {len(source_articles)} 篇已发布文章")
        self.log(f"  目标库中已有 {len(target_article_titles)} 篇文章")

        # 找出需要新增的文章
        new_articles = []
        skipped_articles = []

        for article in source_articles:
            title_lower = article['title'].lower()
            if title_lower in target_article_titles:
                skipped_articles.append(article['title'])
            else:
                new_articles.append(article)

        self.log(f"  发现 {len(new_articles)} 篇新文章")
        if skipped_articles:
            self.log(f"  跳过 {len(skipped_articles)} 篇重复标题的文章")

        # 插入新文章
        for article in new_articles:
            if self.dry_run:
                self.log(f"    [预览] 将新增文章: {article['title']}")
            else:
                # 解析分类ID
                new_category_id = self.category_id_map.get(
                    article['category_id'],
                    article['category_id']  # 如果不在映射中，保持原值
                )

                # 解析作者ID
                new_author_id = self.resolve_author_id(
                    source_conn, target_conn, article['author_id']
                )

                # 插入文章（更新时间戳为同步时间）
                cursor = target_conn.execute(
                    """INSERT INTO blog_article
                       (title, cover, summary, content, status, category_id, author_id,
                        view_roles, edit_roles, view_count, like_count,
                        is_top, is_recommend, published_at, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        article['title'], article['cover'], article['summary'],
                        article['content'], article['status'],
                        new_category_id, new_author_id,
                        article['view_roles'], article['edit_roles'],
                        0, 0,  # 重置阅读数和点赞数
                        article['is_top'], article['is_recommend'],
                        self.sync_time.isoformat(),  # published_at
                        self.sync_time.isoformat(),  # created_at
                        self.sync_time.isoformat()   # updated_at
                    )
                )
                new_id = cursor.lastrowid
                self.article_id_map[article['id']] = new_id
                self.log(f"    ✅ 新增文章: {article['title']} (ID: {new_id})")

            self.stats['articles_added'] += 1

        # 记录跳过的文章
        for title in skipped_articles:
            self.log(f"    ⚠️  跳过: {title} (标题已存在)")
            self.stats['articles_skipped'] += 1

    def sync_article_tags(self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection):
        """同步文章标签关联表"""
        self.log("\n🔗 开始同步文章标签关联...")

        if not self.article_id_map:
            self.log("  没有新文章，跳过标签关联同步")
            return

        # 获取新文章的ID列表
        new_article_ids = list(self.article_id_map.keys())

        # 查询这些文章的标签关联
        source_relations = source_conn.execute(
            """SELECT * FROM blog_article_tag
               WHERE article_id IN ({})""".format(
                   ','.join('?' for _ in new_article_ids)
               ),
            new_article_ids
        ).fetchall()

        self.log(f"  发现 {len(source_relations)} 条标签关联记录")

        # 插入新的关联记录
        added_count = 0
        for relation in source_relations:
            new_article_id = self.article_id_map.get(relation['article_id'])
            new_tag_id = self.tag_id_map.get(relation['tag_id'], relation['tag_id'])

            if not new_article_id:
                continue

            # 检查是否已存在（避免重复插入）
            existing = target_conn.execute(
                "SELECT id FROM blog_article_tag WHERE article_id=? AND tag_id=?",
                (new_article_id, new_tag_id)
            ).fetchone()

            if existing:
                continue

            if self.dry_run:
                self.log(f"    [预览] 将添加关联: 文章ID={new_article_id}, 标签ID={new_tag_id}")
            else:
                target_conn.execute(
                    "INSERT INTO blog_article_tag (article_id, tag_id) VALUES (?, ?)",
                    (new_article_id, new_tag_id)
                )
                added_count += 1

            self.stats['article_tags_added'] += 1

        self.log(f"  新增 {added_count} 条标签关联")

    def update_tag_counts(self, target_conn: sqlite3.Connection):
        """更新标签的文章数量统计"""
        self.log("\n📊 更新标签文章数量统计...")

        tags = target_conn.execute("SELECT id FROM blog_tag").fetchall()

        for tag in tags:
            count = target_conn.execute(
                "SELECT COUNT(*) as cnt FROM blog_article_tag WHERE tag_id=?",
                (tag['id'],)
            ).fetchone()['cnt']

            target_conn.execute(
                "UPDATE blog_tag SET article_count=? WHERE id=?",
                (count, tag['id'])
            )

        self.log(f"  已更新 {len(tags)} 个标签的统计信息")

    def sync(self):
        """执行同步"""
        self.log("=" * 60)
        mode = "预览模式 (dry-run)" if self.dry_run else "实际同步"
        self.log(f"开始{mode}")
        self.log(f"源数据库: {self.source_db}")
        self.log(f"目标数据库: {self.target_db}")
        self.log(f"同步时间: {self.sync_time}")
        self.log("=" * 60)

        try:
            # 连接数据库
            source_conn = self.get_connection(self.source_db)
            target_conn = self.get_connection(self.target_db)

            # 启用事务
            if not self.dry_run:
                target_conn.execute("BEGIN TRANSACTION")

            # 按顺序同步
            self.sync_categories(source_conn, target_conn)
            self.sync_tags(source_conn, target_conn)
            self.sync_articles(source_conn, target_conn)
            self.sync_article_tags(source_conn, target_conn)

            # 更新统计信息
            if not self.dry_run:
                self.update_tag_counts(target_conn)
                target_conn.commit()
                self.log("\n✅ 事务已提交")
            else:
                self.log("\n⚠️  预览模式，未实际写入数据")

            # 输出统计摘要
            self.log("\n" + "=" * 60)
            self.log("同步完成统计:")
            self.log(f"  📁 新增分类: {self.stats['categories_added']}")
            self.log(f"  🏷️  新增标签: {self.stats['tags_added']}")
            self.log(f"  📝 新增文章: {self.stats['articles_added']}")
            self.log(f"  ⚠️  跳过文章: {self.stats['articles_skipped']}")
            self.log(f"  🔗 新增关联: {self.stats['article_tags_added']}")
            self.log("=" * 60)

            # 关闭连接
            source_conn.close()
            target_conn.close()

            return True

        except Exception as e:
            self.log(f"\n❌ 同步失败: {str(e)}")
            if not self.dry_run:
                target_conn.rollback()
                self.log("  事务已回滚")
            raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='运维文档数据库同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 预览模式
  python sync_blog_db.py --source dev.db --target prod.db --dry-run

  # 实际同步
  python sync_blog_db.py --source dev.db --target prod.db
        """
    )

    parser.add_argument(
        '--source', '-s',
        required=True,
        help='源数据库路径（开发环境）'
    )
    parser.add_argument(
        '--target', '-t',
        required=True,
        help='目标数据库路径（生产环境备份）'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='预览模式，不实际写入数据'
    )

    args = parser.parse_args()

    # 创建同步器并执行
    syncer = BlogDatabaseSyncer(
        source_db=args.source,
        target_db=args.target,
        dry_run=args.dry_run
    )

    success = syncer.sync()

    if success:
        exit(0)
    else:
        exit(1)


if __name__ == '__main__':
    main()
