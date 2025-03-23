from sqlmodel import select,desc

from models import dtos,schemas
from dependencies.db import SessionDep

#get activity of user 

async def get_acivities(
    db: SessionDep, username: str, page: int=1, limit: int=5
) -> list[schemas.Activity] :
   offset = (page - 1) * limit

   query = select(schemas.Activity).where(schemas.Activity.receiver_name == username).order_by(desc(schemas.Activity.created_at))
   result = await db.execute(query.offset(offset).limit(limit))

   activities = result.scalars().all()

   return activities