from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from models import security


DATABASE_URL = f"postgresql+asyncpg://{security.database.pg_user}:{security.database.pg_password}@{security.database.pg_host}:{security.database.pg_port}/{security.database.pg_database}"

engine = create_async_engine(DATABASE_URL)


async def startup():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email_trgm ON users USING GIN (email gin_trgm_ops);"))
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

