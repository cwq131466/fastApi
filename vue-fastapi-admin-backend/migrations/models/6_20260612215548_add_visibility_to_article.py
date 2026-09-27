from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "blog_article" ADD "visibility" VARCHAR(20) NOT NULL  DEFAULT 'private' /* 可见性 */;
        CREATE INDEX "idx_blog_articl_visibil_6ca92f" ON "blog_article" ("visibility");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_blog_articl_visibil_6ca92f";
        ALTER TABLE "blog_article" DROP COLUMN "visibility";"""
