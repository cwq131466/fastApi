from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "script_run_logs" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "time" TIMESTAMP NOT NULL  /* 执行时间 */,
    "level" VARCHAR(20) NOT NULL  /* 日志级别 */,
    "info" TEXT NOT NULL  /* 日志信息 */,
    "cmd" TEXT   /* 执行的命令\/脚本 */,
    "ip" VARCHAR(45) NOT NULL  /* IP地址 */,
    "os" VARCHAR(100)   /* 操作系统 */,
    "kernel" VARCHAR(100)   /* 内核版本 */,
    "mac" VARCHAR(17)   /* MAC地址 */,
    "username" VARCHAR(64)   /* 用户名 */
) /* 脚本执行日志表 */;
CREATE INDEX IF NOT EXISTS "idx_script_run__created_c47711" ON "script_run_logs" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_script_run__updated_b6c5dc" ON "script_run_logs" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_script_run__time_bfdb19" ON "script_run_logs" ("time");
CREATE INDEX IF NOT EXISTS "idx_script_run__level_40fa5a" ON "script_run_logs" ("level");
CREATE INDEX IF NOT EXISTS "idx_script_run__ip_bd6467" ON "script_run_logs" ("ip");
CREATE INDEX IF NOT EXISTS "idx_script_run__mac_711bfb" ON "script_run_logs" ("mac");
CREATE INDEX IF NOT EXISTS "idx_script_run__usernam_9c5b74" ON "script_run_logs" ("username");
        CREATE TABLE IF NOT EXISTS "uploaded_file" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "filename" VARCHAR(255) NOT NULL  /* 文件名 */,
    "original_filename" VARCHAR(255) NOT NULL  /* 原始文件名 */,
    "display_name" VARCHAR(255)   /* 显示名称\/关联文件名 */,
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
        DROP TABLE IF EXISTS "uploaded_file";
        DROP TABLE IF EXISTS "script_run_logs";"""
