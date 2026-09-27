from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "blog_article" ADD "shared_roles" JSON;
        ALTER TABLE "blog_article_revision" ADD "shared_roles" JSON;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "blog_article" DROP COLUMN "shared_roles";
        ALTER TABLE "blog_article_revision" DROP COLUMN "shared_roles";"""
