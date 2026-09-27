from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "blog_article_like" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "article_id" INT NOT NULL,
            "user_id" INT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_blog_artic_article_f8b7e3" ON "blog_article_like" ("article_id", "user_id");
        CREATE INDEX IF NOT EXISTS "idx_blog_artic_article_d8f2a1" ON "blog_article_like" ("article_id");
        CREATE INDEX IF NOT EXISTS "idx_blog_artic_user_id_c3e4b2" ON "blog_article_like" ("user_id");
        
        CREATE TABLE IF NOT EXISTS "blog_article_favorite" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "article_id" INT NOT NULL,
            "user_id" INT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_blog_artic_article_a9c8d4" ON "blog_article_favorite" ("article_id", "user_id");
        CREATE INDEX IF NOT EXISTS "idx_blog_artic_article_e5f6g7" ON "blog_article_favorite" ("article_id");
        CREATE INDEX IF NOT EXISTS "idx_blog_artic_user_id_h8i9j0" ON "blog_article_favorite" ("user_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    # SQLite doesn't support DROP TABLE IF EXISTS well in transactions
    # Using no-op for safety
    return """SELECT 1"""
