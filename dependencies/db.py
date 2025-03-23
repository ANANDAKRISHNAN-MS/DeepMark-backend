from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from database import engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        try:
            yield session
        finally:
            await session.close()

SessionDep = Annotated[AsyncSession, Depends(get_session)]