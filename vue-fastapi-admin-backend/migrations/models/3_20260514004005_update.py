from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "script" DROP COLUMN "uploaded_files";
        CREATE TABLE IF NOT EXISTS "uploaded_file" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "filename" VARCHAR(255) NOT NULL  /* 文件名 */,
    "original_filename" VARCHAR(255) NOT NULL  /* 原始文件名 */,
    "file_path" VARCHAR(500) NOT NULL UNIQUE /* 文件相对路径 */,
    "file_size" BIGINT NOT NULL  DEFAULT 0 /* 文件大小（字节） */,
    "file_type" VARCHAR(50)   /* 文件类型\/扩展名 */,
    "mime_type" VARCHAR(100)   /* MIME类型 */,
    "uploaded_by" INT   /* 上传者ID */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否有效 */,
    "script_id" BIGINT REFERENCES "script" ("id") ON DELETE SET NULL /* 关联的脚本 */
) /* 上传文件元数据表 */;
CREATE INDEX IF NOT EXISTS "idx_uploaded_fi_created_164f68" ON "uploaded_file" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_uploaded_fi_updated_25b6d2" ON "uploaded_file" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_uploaded_fi_filenam_a95482" ON "uploaded_file" ("filename");
CREATE INDEX IF NOT EXISTS "idx_uploaded_fi_file_pa_28d5b8" ON "uploaded_file" ("file_path");
CREATE INDEX IF NOT EXISTS "idx_uploaded_fi_is_acti_db0341" ON "uploaded_file" ("is_active");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "script" ADD "uploaded_files" JSON   /* 上传的文件路径列表 */;
        DROP TABLE IF EXISTS "uploaded_file";"""
