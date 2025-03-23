from fastapi import APIRouter,status,HTTPException,Depends

from dependencies import db as database, token
from models import dtos
from services import profile , auth

router = APIRouter(
    prefix="/profile",
    tags=["profile"]
)

#get logged user profile

@router.post("/",response_model=dtos.Profile)
async def get_profile(access_token: str, db: database.SessionDep):
    #verift token
    curr_user = await token.verify_token(db, access_token)
    profile = dtos.Profile.from_orm(curr_user)

    return profile


#get user profile

@router.post("/user",response_model=dtos.Profile)
async def get_user_profile(access_token: str, username:str, db: database.SessionDep):
    #verify token
    curr_user = await token.verify_token(db, access_token)

    db_user = await auth.existing_user(db, username, "")
    profile = dtos.Profile.from_orm(db_user)

    return profile

#follow user 

@router.post("/follow",status_code=status.HTTP_204_NO_CONTENT)
async def follow(access_token: str, username:str, db: database.SessionDep):
    #verify token
    curr_user = await token.verify_token(db, access_token)

    res, detail = await profile.follow(db, curr_user.username, username)

    if res == False:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=detail)


#unfollow user

@router.post("/unfollow",status_code=status.HTTP_204_NO_CONTENT)
async def unfollow(access_token: str, username:str, db: database.SessionDep):
    #verify token
    curr_user= await token.verify_token(db, access_token)

    res, detail = await profile.unfollow(db, curr_user.username, username)

    if res == False:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=detail)
    


#get followers

@router.post("/followers", response_model=dtos.FollowersList)
async def get_followers(
    db: database.SessionDep,
    access_token: str = Depends(token.oauth2_bearer)
):

    #verify token
    curr_user= await token.verify_token(db, access_token)
    db_followers = await profile.get_followers(db, curr_user.user_id)

    return dtos.FollowersList(followers=db_followers)


#get following

@router.post("/following", response_model=dtos.FollowingList)
async def get_following(
    db: database.SessionDep,
    access_token: str = Depends(token.oauth2_bearer)
):
    #verify token
    curr_user= await token.verify_token(db, access_token)
    db_following = await profile.get_following(db, curr_user.user_id)
    
    return dtos.FollowingList(following=db_following)