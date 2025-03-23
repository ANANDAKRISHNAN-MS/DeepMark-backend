from fastapi import APIRouter,Depends

from dependencies import db as database, token
from services import activity

router = APIRouter(
    prefix="/activity",
    tags=["activity"]
)

@router.post("/")
async def get_activities(
    db: database.SessionDep,
    page: int = 1,
    limit: int = 5,
    access_token: str = Depends(token.oauth2_bearer)
):
    #verify token
    curr_user = await token.verify_token(db,access_token)

    return await activity.get_acivities(db, curr_user.username, page, limit)

