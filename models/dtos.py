from fastapi import UploadFile,File,Form
from pydantic import BaseModel, Field,validator,EmailStr
from typing import Optional
from datetime import datetime

#User Pydantic Models

class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    email: EmailStr 
    profile_picture: Optional[str] = None
    bio: Optional[str] = None

    @validator('username')
    def validate_usrname(cls,v):
        if not v:
            raise ValueError('Enter a Valid Username')
        return v
   
    @validator('name')
    def validate_name(cls,v):
        if not v or not v.replace(" ", "").isalpha():
            raise ValueError('Name must contain only alphabetic characters')
        return v
    

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    
class UserUpdate(BaseModel):
    name: Optional[str] = Form(None)
    profile_picture: Optional[UploadFile] = File(None)
    bio: Optional[str] = Form(None)

class UserDtos(UserBase):
    user_id: int
    following_count: int 
    followers_count: int 
    
    model_config = {
        "from_attributes": True 
    }


       

#Posts Pydantic Models

class Hashtag(BaseModel):
    id: int
    name: str

class PostCreate(BaseModel):
    media_url: str = Field(..., max_length=255)
    caption: Optional[str] = Field(None, max_length=500)
    media_type: str = Field(..., pattern="^(image|video)$")

class Post(PostCreate):
    id: int
    user_id: int
    likes_count: int
    created_at: datetime

    model_config = {
        "from_attributes": True 
    }


#Activities Pydantic Models

class ActivityBase(BaseModel):
    sender_name: str
    receiver_name: str

class LikeActivityCreate(ActivityBase):
    like_post_url: str
    like_post_id: int

class DetectionActivityCreate(ActivityBase):
    dectected_post_url: str
    detected_post_id: int

class Activity(ActivityBase):
    created_at: datetime 
   
    model_config = {
        "from_attributes": True 
    }


# Profile Pydantic Models

class Profile(UserBase):
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0

    model_config = {
        "from_attributes": True 
    }

class ProfileUserSchema(BaseModel):
    profile_picture: Optional[str] = None
    username: str
    user_id: int
    
    model_config = {
        "from_attributes": True 
    }

class FollowingList(BaseModel):
    following: list[ProfileUserSchema] = []

    model_config = {
        "from_attributes": True 
    }

class FollowersList(BaseModel):
    followers: list[ProfileUserSchema] = []
       
    model_config = {
        "from_attributes": True 
    }

 
