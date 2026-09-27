from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "script" ADD "uploaded_files" JSON   /* 上传的文件路径列表 */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "script" DROP COLUMN "uploaded_files";"""
