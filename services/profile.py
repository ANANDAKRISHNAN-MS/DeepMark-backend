from sqlmodel import select
from sqlalchemy import and_
from typing import Optional


from dependencies.db import SessionDep
from models import schemas,dtos
from . import auth


# follow 
async def follow(db: SessionDep, follower: str, following: str):
    db_follower = await auth.existing_user(db, follower, "")
    db_following = await auth.existing_user(db, following, "")
    
    db_follow = await check_follow(db, db_follower, db_following)

    if db_follow:
        return False , "already following"
    
    db_follow = schemas.Follower(follower_id=db_follower.user_id, following_id=db_following.user_id)
    db.add(db_follow)

    db_follower.following_count+=1
    db_following.followers_count+=1

    #creating activity

    follow_activity = schemas.Activity(
        receiver_name=db_following.username,
        sender_name=db_follower.username,
        followed_profile_picture=db_follower.profile_picture
    )
    db.add(follow_activity)

    await db.commit()
    return True, "followed"
# unfollow 

async def unfollow(db: SessionDep, follower: str, following: str):
    db_follower = await auth.existing_user(db, follower, "")
    db_following = await auth.existing_user(db, following, "")
    
    db_follow = await check_follow(db, db_follower,db_following)

    if not db_follow:
        return False , "does not follow"

    await db.delete(db_follow)

    db_follower.following_count-=1
    db_following.followers_count-=1

    await db.commit()

# get followers

async def get_followers(db: SessionDep, user_id: int) -> list[dtos.ProfileUserSchema]:
    db_user = await auth.get_user_from_user_id(db, user_id)
    if not db_user:
        return []
    
    result = await db.execute(
                select(schemas.User)
                .join(schemas.Follower, schemas.Follower.follower_id == schemas.User.user_id)
                .where(schemas.Follower.following_id == user_id)
                
            )
    
    db_follower = result.scalars().all()
    follower_list = []
    for follower in db_follower:
        user = dtos.ProfileUserSchema(
            profile_picture=follower.profile_picture,
            username=follower.username,
            user_id=follower.user_id
        )
        follower_list.append(user)

    return follower_list

#get following

async def get_following(db: SessionDep, user_id: int) -> list[dtos.ProfileUserSchema]:
    db_user = await auth.get_user_from_user_id(db, user_id)
    if not db_user:
        return []
    
    result = await db.execute(
                select(schemas.User)
                .join(schemas.Follower, schemas.Follower.following_id == schemas.User.user_id )
                .where(schemas.Follower.follower_id == user_id)
            )

    db_following = result.scalars().all()
    following_list = []
    for following in db_following:
        user = dtos.ProfileUserSchema(
            profile_picture=following.profile_picture,
            username=following.username,
            user_id=following.user_id
        )
        following_list.append(user)

    return following_list

#check follow

async def check_follow(
        db: SessionDep, db_follower: Optional[schemas.User], db_following: Optional[schemas.User]
):
    if not db_follower or not db_following:
        return False," user does not exist"
   
    result = await db.execute(
        select(schemas.Follower).
        where(and_(schemas.Follower.follower_id == db_follower.user_id, schemas.Follower.following_id == db_following.user_id))
    )

    db_follow = result.scalar_one_or_none()

    return db_follow is not None
    
    
