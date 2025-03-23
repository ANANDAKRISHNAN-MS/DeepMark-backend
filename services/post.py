from fastapi import UploadFile,File,HTTPException,status
from sqlmodel import select,desc
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from typing import List
import re

from . import process
from dependencies.db import SessionDep
from models import dtos,schemas
from . import auth,upload

# creating hastag from post
async def create_hashtag(db: SessionDep, post: schemas.Post):
    regex = r"#\w+"
    matches = re.findall(regex, post.caption)

    for match in matches:
        name = match[1:]

        result = await db.execute(select(schemas.Hashtag).where(schemas.Hashtag.name == name))
        hashtag = result.scalar_one_or_none()

        if not hashtag :
            hashtag = schemas.Hashtag(name=name)
            db.add(hashtag)
            await db.commit()
        post.hashtags.append(hashtag)
  



# create post

async def create_post(
        db: SessionDep,
        media: UploadFile,
        post: dtos.PostCreate,
        user: schemas.User
):
    curr_user_id = user.user_id
    curr_username = user.username
    curr_profile_picture = user.profile_picture

    hashed_value = await process.process_media(db, media, user)
    deepmark_result = await process.add_attributes(media, user)

    media_url = await upload.upload_file(
        user.username,
        deepmark_result["metadata_value"],
        deepmark_result["final_media"]
    )

    db_post = schemas.Post(
        caption=post.caption,
        media_url=media_url,
        media_type=post.media_type,
        user_id=curr_user_id
    )

    post_obj = dtos.PostCreate(
        media_type=db_post.media_type,
        media_url=db_post.media_url
    )

    await create_hashtag(db, db_post)

    db.add(db_post)

    await db.commit()
    await db.refresh(db_post)
    
    db_dmm = schemas.DMM(
        dmm_id=deepmark_result["dmm_id"],
        video_id=db_post.id,
        hash_value=hashed_value
    )

    try:
        db.add(db_dmm)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        await upload.delete_file(curr_username, post_obj.media_url, post_obj.media_type)
        await db.delete(db_post)
        await db.commit()
        result = await db.execute(
            select(schemas.Post, schemas.User)
            .select_from(schemas.DMM)
            .join(schemas.Post, schemas.DMM.video_id == schemas.Post.id)
            .join(schemas.User, schemas.User.user_id == schemas.Post.user_id)
            .where(schemas.DMM.hash_value == hashed_value)
        )
        data = result.first()
        post, post_user = data
        if post_user.user_id == curr_user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="post was already uploaded"
            )
        detected_activity = schemas.Activity(
            receiver_name=post_user.username,
            sender_name=curr_username,
            media_type=post.media_type,
            detected_user_profile_picture=curr_profile_picture,  
            detected_post_id=post.id,
            detected_post_url=post.media_url
        )
        db.add(detected_activity)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f'you don\'t own this media'
        )
    
    await db.refresh(db_post)
    return db_post


# get user post

async def get_user_post(db: SessionDep, user_id: int) -> List[dtos.Post]:
    result = await db.execute(
        select(schemas.Post).where(schemas.Post.user_id == user_id).order_by(desc(schemas.Post.created_at))
    )
    posts = result.scalars().all()
    return posts



# get post from hashtags

async def get_posts_from_hashtags(db: SessionDep, hashtag_name: str):
   result = await db.execute(select(schemas.Hashtag).where(schemas.Hashtag.name == hashtag_name))
   hashtag = result.scalar_one_or_none() 
   
   if not hashtag:
       return None
   
   await db.refresh(hashtag, ["posts"])
   return hashtag.posts



# get random posts for feed

async def get_random_posts(
    db: SessionDep,
    user: schemas.User, 
    page: int = 1,
    limit: int = 10,
    hashtag: str = None
):
    result = await db.execute(select(func.count(schemas.Post.id)))
    total_posts = result.scalar() or 0

    offset = (page - 1) * limit
    if offset >= total_posts:
        return[]

    query = select(schemas.Post, schemas.User.username,schemas.User.profile_picture).join(schemas.User)

    if hashtag : 
        query = query.join(schemas.PostHashtag).join(schemas.Hashtag).where(schemas.Hashtag.name == hashtag)
    
    query = query.order_by(desc(schemas.Post.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    posts = result.all()
    post_list = []
    for post, username, profile_picture in posts:
        post_dict = post.dict()  
        post_dict["username"] = username
        post_dict["user_profile_picture"] = profile_picture
        
        await db.refresh(post, ["liked_by_users"])

        if user in post.liked_by_users:
            post_dict['isLiked'] = True
        else:
            post_dict['isLiked'] = False

        
        post_list.append(post_dict)

    return post_list


# get post from post_id

async def get_post_from_post_id(db: SessionDep, post_id: int) -> dtos.Post:
    result = await db.execute(select(schemas.Post).where(schemas.Post.id == post_id))
    post = result.scalar_one_or_none()

    return post



# delete from post_id:

async def delete_from_post_id(db: SessionDep, post_id: int):
    post = await get_post_from_post_id(db, post_id)
    if post:
        await db.delete(post)
        await db.commit()



# like post

async def like_post(db: SessionDep, post_id: int, username: str):
    post = await get_post_from_post_id(db,post_id)
    if not post:
        return False, "invalid post id"
    
    user = await auth.existing_user(db, username, "")
    if not user:
        return False, "invalid username"
    
    await db.refresh(post, ["liked_by_users","user"])

    if user in post.liked_by_users:
        return False, "already liked"
    
    post.liked_by_users.append(user)
    post.likes_count = len(post.liked_by_users)

    like_activity = schemas.Activity(
        receiver_name=post.user.username,
        media_type=post.media_type,
        sender_name=username,
        liked_user_profile_picture=user.profile_picture,
        liked_post_id=post_id,
        liked_post_url=post.media_url
    )
    db.add(like_activity)
    await db.commit()

    return True, "done"


# unlike post

async def unlike_post(db: SessionDep, post_id: int, username:str):
    post = await get_post_from_post_id(db,post_id)
    if not post:
        return False, "invalid post id"
    
    user = await auth.existing_user(db, username, "")
    if not user:
        return False, "invalid username"
    
    await db.refresh(post, ["liked_by_users"])

    if not user in post.liked_by_users:
        return False, "already not liked"

    post.liked_by_users.remove(user)
    post.likes_count = len(post.liked_by_users)

    await db.commit() 

    return True, "done"

# users who liked the post
async def liked_user_post(db: SessionDep, post_id: int) -> List[dtos.ProfileUserSchema]:
    post = await get_post_from_post_id(db, post_id)
    if not post:
        return []
    
    await db.refresh(post, ["liked_by_users"])

    liked_users = post.liked_by_users

    return liked_users








