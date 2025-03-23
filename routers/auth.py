from fastapi import APIRouter,HTTPException,status,Depends,Form,UploadFile,File
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm

from models import dtos
from dependencies import db as database , token 
from services import auth


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


#signup
@router.post('/signup',status_code=status.HTTP_201_CREATED)
async def create_user(user: dtos.UserCreate, db: database.SessionDep):

    try:
        #check for existing user
        db_user = await auth.existing_user(db, user.username, user.email)
        if db_user : 
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="username or email already in use"
            )
        
        db_user = await auth.create_new_user(db, user)
    
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

#login to generate token
@router.post('/token',status_code=status.HTTP_202_ACCEPTED)
async def login(db: database.SessionDep, form_data: OAuth2PasswordRequestForm = Depends()):
    db_user = await auth.authenticate(db, form_data.username, form_data.password)
    if not db_user : 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = await token.create_access_token(db_user.username,db_user.user_id)
    return {
            "access_token" : access_token,
            "token_type" : "bearer" , 
            "username" : db_user.username,
        }

#get current user
@router.get("/profile",status_code=status.HTTP_200_OK,response_model=dtos.UserDtos)
async def current_user(db: database.SessionDep,access_token: str = Depends(token.oauth2_bearer)):
    db_user = await token.verify_token(db, access_token)
    if not db_user : 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )
    return db_user

#update user
@router.put("/{username}",status_code=status.HTTP_204_NO_CONTENT)
async def update_user(
    db: database.SessionDep,
    username: str,
    access_token: str = Depends(token.oauth2_bearer),
    name: Optional[str] = Form(None),
    profile_picture: Optional[UploadFile] = File(None),
    bio: Optional[str] = Form(None),
):
    db_user = await token.verify_token(db, access_token)

    if db_user.username != username :
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this user"
        )
    user_update = {
        "name":name,
        "profile_picture":profile_picture,
        "bio":bio
    }
    await auth.update_user(db, db_user, user_update)

    