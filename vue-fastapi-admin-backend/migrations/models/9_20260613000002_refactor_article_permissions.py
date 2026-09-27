from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "blog_article" ADD "view_roles" JSON NOT NULL DEFAULT '[]';
        ALTER TABLE "blog_article" ADD "edit_roles" JSON NOT NULL DEFAULT '[]';
        ALTER TABLE "blog_article_revision" ADD "view_roles" JSON NOT NULL DEFAULT '[]';
        ALTER TABLE "blog_article_revision" ADD "edit_roles" JSON NOT NULL DEFAULT '[]';
        ALTER TABLE "blog_article" DROP COLUMN "visibility";
        ALTER TABLE "blog_article" DROP COLUMN "shared_roles";
        ALTER TABLE "blog_article_revision" DROP COLUMN "visibility";
        ALTER TABLE "blog_article_revision" DROP COLUMN "shared_roles";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "blog_article" ADD "visibility" VARCHAR(20) NOT NULL DEFAULT 'private';
        ALTER TABLE "blog_article" ADD "shared_roles" JSON;
        ALTER TABLE "blog_article_revision" ADD "visibility" VARCHAR(20);
        ALTER TABLE "blog_article_revision" ADD "shared_roles" JSON;
        ALTER TABLE "blog_article" DROP COLUMN "view_roles";
        ALTER TABLE "blog_article" DROP COLUMN "edit_roles";
        ALTER TABLE "blog_article_revision" DROP COLUMN "view_roles";
        ALTER TABLE "blog_article_revision" DROP COLUMN "edit_roles";"""
