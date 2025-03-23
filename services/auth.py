from fastapi import UploadFile
from sqlmodel import select

from models import schemas,dtos
from hashing import Hash
from encryption import Encrypt
from dependencies.db import SessionDep
from . import upload

#check for existing user

async def existing_user(db: SessionDep, username: str, email: str):
    result = await db.execute(select(schemas.User).where(schemas.User.username == username))
    user = result.scalar_one_or_none()
    if user:
       return user 
    result = await db.execute(select(schemas.User).where(schemas.User.email == email))
    user = result.scalar_one_or_none()
    return user

#get user from user_id
async def get_user_from_user_id(db: SessionDep, user_id: int):
    result = await db.execute(select(schemas.User).where(schemas.User.user_id == user_id))
    user = result.scalar_one_or_none()
    return user

#create user
async def create_new_user(db: SessionDep, user: dtos.UserCreate):
    try:
        db_user = schemas.User(**user.dict())
        db_user.password_hash = await Hash.bcrypt(user.password)
        db_user.security_key = await Encrypt.generate_user_key()
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except:
        return None

#authentication
async def authenticate(db: SessionDep, username: str, password: str):
    db_user = await existing_user(db, username, "")
    if not db_user or not await Hash.verify_pass(password, db_user.password_hash):
        return None
    return db_user

#update user
async def update_user(db: SessionDep, db_user: dtos.UserDtos, user_update: dtos.UserUpdate):
    db_user.bio = user_update.get("bio") or db_user.bio
    db_user.name = user_update.get("name") or db_user.name
    if user_update.get("profile_picture"):
        profile_pic_url =  await upload.upload_file(db_user.username, user_update.profile_picture)
        db_user.profile_picture = profile_pic_url

    await db.commit()
