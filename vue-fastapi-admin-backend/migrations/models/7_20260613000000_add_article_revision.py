from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "blog_article_revision" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "article_id" INT NOT NULL  /* 文章ID */,
    "editor_id" INT NOT NULL  /* 编辑人ID */,
    "editor_name" VARCHAR(50) NOT NULL  /* 编辑人姓名 */,
    "title" VARCHAR(200) NOT NULL  /* 标题快照 */,
    "content" TEXT NOT NULL  /* 内容快照 */,
    "summary" TEXT   /* 摘要快照 */,
    "cover" VARCHAR(500)   /* 封面快照 */,
    "category_id" INT NOT NULL  /* 分类ID快照 */,
    "visibility" VARCHAR(20) NOT NULL  /* 可见性快照 */,
    "tag_ids" JSON NOT NULL  DEFAULT '[]' /* 标签ID快照 */,
    "changes" JSON NOT NULL  DEFAULT '{}' /* 变更内容 */,
    "change_summary" VARCHAR(500)   /* 变更摘要 */
) /* 文章编辑记录表 */;
CREATE INDEX IF NOT EXISTS "idx_blog_articl_created_8f9a2c" ON "blog_article_revision" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_updated_4b7e1d" ON "blog_article_revision" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_article_3c8f5a" ON "blog_article_revision" ("article_id");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_editor__6d2e9b" ON "blog_article_revision" ("editor_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_blog_articl_created_8f9a2c";
        DROP INDEX IF EXISTS "idx_blog_articl_updated_4b7e1d";
        DROP INDEX IF EXISTS "idx_blog_articl_article_3c8f5a";
        DROP INDEX IF EXISTS "idx_blog_articl_editor__6d2e9b";
        DROP TABLE IF EXISTS "blog_article_revision";"""
