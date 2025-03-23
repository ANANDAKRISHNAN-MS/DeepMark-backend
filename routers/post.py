from fastapi import APIRouter,HTTPException,status,UploadFile,File,Form,Depends
from typing import Optional

from models import dtos
from dependencies import db as database , token 
from services import post,auth

router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)


#create post

@router.post("/",response_model=dtos.Post, status_code=status.HTTP_201_CREATED)
async def create_post(
    db: database.SessionDep,
    media: UploadFile = File(...),
    caption: Optional[str] = Form(None, max_length=500),
    media_type: str = Form(..., regex="^(image|video)$"),
    access_token: str = Depends(token.oauth2_bearer),
):
    #verify token
    curr_user = await token.verify_token(db, access_token)

    db_post = dtos.PostCreate(
        media_url="",
        caption=caption,
        media_type=media_type
    )
    db_post = await post.create_post(db, media, db_post, curr_user)
    return db_post



#get posts of the logged user

@router.post("/user", response_model=list[dtos.Post])
async def get_current_user_posts(
    db: database.SessionDep,
    access_token: str = Depends(token.oauth2_bearer)
):
    #verify token
    curr_user = await token.verify_token(db, access_token)
    
    return await post.get_user_post(db, curr_user.user_id)


#get posts a of a particular user

@router.get("/user/{username}", response_model=list[dtos.Post])
async def get_user_post(
    username: str,
    db: database.SessionDep,
    access_token: str = Depends(token.oauth2_bearer)
):
    #verify token
    curr_user = await token.verify_token(db, access_token)

    user = await auth.existing_user(db, username, "")

    return await post.get_user_post(db, user.user_id)


#get posts according to hashtag

@router.get("/hastag/{hashtag}")
async def get_post_from_hashtag(
    hashtag: str,
    db: database.SessionDep,
    access_token: str = Depends(token.oauth2_bearer)
):
    #verify token
    curr_user = await token.verify_token(db, access_token)

    return await post.get_posts_from_hashtags(db, hashtag)


#get posts for feed

@router.get("/feed")
async def get_random_posts(
   db: database.SessionDep,
   page: int = 1,
   limit: int = 5,
   hashtag: str = None,
   access_token: str = Depends(token.oauth2_bearer)
):
    #verify token
    curr_user = await token.verify_token(db, access_token)

    return await post.get_random_posts(db, curr_user, page, limit, hashtag)


#delete a post
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: database.SessionDep,
    access_token: str = Depends(token.oauth2_bearer)
):
    #verify token
    curr_user = await token.verify_token(db, access_token)

    db_post = await post.get_post_from_post_id(db, post_id)
    if db_post.user_id != curr_user.user_id:
        raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED, detail="you are not authorized to delte this post"
        )
    await post.delete_from_post_id(db, post_id)


#like a post

@router.post("/like", status_code=status.HTTP_204_NO_CONTENT)
async def like_post(
    db: database.SessionDep,
    post_id: int = Form(...),
    access_token: str = Depends(token.oauth2_bearer)    
):
   #verify token
   curr_user = await token.verify_token(db, access_token) 

   res, detail = await post.like_post(db, post_id, curr_user.username)
   if res == False :
       raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


#unlike a post

@router.post("/unlike", status_code=status.HTTP_204_NO_CONTENT)
async def like_post(
    db: database.SessionDep,
    post_id: int = Form(...),
    access_token: str = Depends(token.oauth2_bearer)  
):
   #verify token
   curr_user = await token.verify_token(db, access_token) 

   res, detail = await post.unlike_post(db, post_id, curr_user.username)
   if res == False :
       raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)    


#likes on a particular post
@router.get("/likes/{post_id}", response_model=list[dtos.ProfileUserSchema])
async def users_like_post(
    post_id: int,
    db: database.SessionDep,
    access_token: str = Depends(token.oauth2_bearer)
):
   #verify token
   curr_user = await token.verify_token(db, access_token)

   return await post.liked_user_post(db, post_id)


#get post

@router.get("/{post_id}",response_model=dtos.Post)
async def get_post(
    post_id: int,
    db: database.SessionDep,
    access_token: str = Depends(token.oauth2_bearer)
):
    #verify token
   curr_user = await token.verify_token(db, access_token) 

   db_post= await post.get_post_from_post_id(db, post_id)
   if not db_post:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=" invalid post id")
   
   return db_post 





