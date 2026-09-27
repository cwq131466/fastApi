from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """ALTER TABLE "user" ADD "avatar" VARCHAR(500) NULL"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    # SQLite doesn't support DROP COLUMN in older versions
    # Just a no-op for downgrade
    return """SELECT 1"""
