from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "script_category" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(50) NOT NULL  /* 分类名称 */,
    "parent_id" INT NOT NULL  DEFAULT 0 /* 父分类ID */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */
) /* 运维脚本分类表 */;
CREATE INDEX IF NOT EXISTS "idx_script_cate_created_305b14" ON "script_category" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_script_cate_updated_3aac44" ON "script_category" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_script_cate_name_57ba4e" ON "script_category" ("name");
CREATE INDEX IF NOT EXISTS "idx_script_cate_parent__849fb7" ON "script_category" ("parent_id");
CREATE INDEX IF NOT EXISTS "idx_script_cate_order_5333bc" ON "script_category" ("order");
CREATE INDEX IF NOT EXISTS "idx_script_cate_is_acti_638da4" ON "script_category" ("is_active");
        CREATE TABLE IF NOT EXISTS "script" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "title" VARCHAR(100) NOT NULL  /* 脚本标题 */,
    "requirements" JSON   /* 安装要求列表 */,
    "steps" JSON NOT NULL  /* 安装步骤（键值对） */,
    "features" TEXT   /* 主要功能描述 */,
    "reference_links" JSON   /* 参考资料链接 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */,
    "category_id" BIGINT NOT NULL REFERENCES "script_category" ("id") ON DELETE CASCADE
) /* 运维脚本表 */;
CREATE INDEX IF NOT EXISTS "idx_script_created_a1aaed" ON "script" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_script_updated_20fb93" ON "script" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_script_title_fcb8e4" ON "script" ("title");
CREATE INDEX IF NOT EXISTS "idx_script_order_9a56d8" ON "script" ("order");
CREATE INDEX IF NOT EXISTS "idx_script_is_acti_916c8e" ON "script" ("is_active");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "script_category";
        DROP TABLE IF EXISTS "script";"""
