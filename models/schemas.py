from typing import Optional, List, Literal
from sqlmodel import Field, SQLModel, Index, UniqueConstraint, CheckConstraint, Relationship
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime,Integer,ForeignKey,CHAR
from uuid import UUID, uuid4

#Association Tables

class PostLikes(SQLModel, table=True):
    __tablename__ = "post_likes"

    user_id: Optional[int] = Field(
        default=None, foreign_key="users.user_id", primary_key=True
    )
    post_id: Optional[int] = Field(
        default=None, foreign_key="posts.id", primary_key=True
    )

class PostHashtag(SQLModel, table=True):
    __tablename__ = "post_hashtag"

    post_id: Optional[int] = Field(
        default=None, foreign_key="posts.id", primary_key=True
    )
    hashtag_id: Optional[int] = Field(
        default=None, foreign_key="hashtags.id", primary_key=True
    )


#Database table schemas

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_username", "username"),
        UniqueConstraint("email", name="unique_email"),
        UniqueConstraint("username", name="unique_username"),
        CheckConstraint("warning <= 3", name="check_warning_limit"),
    )

    user_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)  
    username: str = Field(max_length=50)
    email: str = Field(max_length=100)
    password_hash: str = Field(max_length=255)
    security_key: str = Field(max_length=255)
    profile_picture: str = Field(
        default="user_default", 
        max_length=255
    )  
    bio: Optional[str] = Field(default="",max_length=250)
    warning: int = Field(default=0)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    following_count: int = Field(default=0)
    followers_count: int = Field(default=0)

    posts: List["Post"] = Relationship(back_populates="user")
    liked_posts: List["Post"] = Relationship(
        back_populates="liked_by_users", link_model=PostLikes
    )
    followers: List["Follower"] = Relationship(
        back_populates="following",
        sa_relationship_kwargs={"foreign_keys": "Follower.following_id"}
    )
    following: List["Follower"] = Relationship(
        back_populates="follower",
        sa_relationship_kwargs={"foreign_keys": "Follower.follower_id"}
    )


class Post(SQLModel, table=True):
    __tablename__ = "posts"

    __table_args__ = (
        Index("idx_posts_user_id", "user_id"),
        Index("idx_posts_media_type", "media_type"),
        Index("idx_posts_created_at", "created_at"),
        UniqueConstraint("media_url", name="unique_media_url"),
        CheckConstraint("media_type IN ('image', 'video')", name="check_media_type"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(sa_column=Column(Integer, ForeignKey("users.user_id")))
    media_url: str = Field(max_length=255)
    caption: Optional[str] = Field(default="",max_length=500)
    likes_count: int = Field(default=0)
    media_type: str = Field(max_length=10)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )

    user: User = Relationship(back_populates="posts")
    hashtags: List["Hashtag"] = Relationship(
        back_populates="posts", link_model=PostHashtag
    )
    liked_by_users: List["User"] = Relationship(
        back_populates="liked_posts", link_model=PostLikes
    )

class Hashtag(SQLModel, table = True):
    __tablename__ = "hashtags"
    __table_args__ = (
        Index("idx_hashtag_id", "id"),
        Index("idx_hashtag_name", "name")
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    

    posts: List["Post"] = Relationship(
        back_populates="hashtags", link_model=PostHashtag
    )

class Follower(SQLModel, table=True):
    __tablename__ = "followers"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="unique_follow"),
        CheckConstraint("follower_id != following_id", name="check_no_self_follow"),
    )

    follower_id: Optional[int] = Field(default=None, foreign_key="users.user_id", primary_key=True)
    following_id: Optional[int] = Field(default=None, foreign_key="users.user_id", primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )

    follower: User = Relationship(
        back_populates="following",
        sa_relationship_kwargs={"foreign_keys": "[Follower.follower_id]"}
    )
    following: User = Relationship(
        back_populates="followers",
        sa_relationship_kwargs={"foreign_keys": "[Follower.following_id]"}
    )


class Activity(SQLModel, table=True):
    __tablename__ = "activities"
    __table_args__ = (
        Index("idx_notifications_receiver_name", "receiver_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    receiver_name: Optional[str] = Field(foreign_key="users.username")
    sender_name: Optional[str] = Field(default=None,foreign_key="users.username")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True ), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    media_type: str = Literal["image", "video"]

    #like activity
    liked_post_id: Optional[int] = Field(default=None,foreign_key="posts.id")
    liked_post_url: Optional[str] = Field(default="",max_length=255)
    liked_user_profile_picture:Optional[str] = Field(default="", max_length=255) 
    
    #follow activity:
    followed_profile_picture:Optional[str] = Field(default="", max_length=255)  

    #deepfake dectected activity
    detected_post_id: Optional[int] = Field(default=None,foreign_key="posts.id")
    detected_post_url: Optional[str] = Field(default="",max_length=255)
    detected_user_profile_picture:Optional[str] = Field(default="", max_length=255)


class DMM(SQLModel, table=True):
    __tablename__ = "dmm"
    __table_args__ = (
        Index("idx_dmm_video_id", "video_id"),
        UniqueConstraint("hash_value", name="unique_hash_value"),
    )

    dmm_id: str = Field(
        sa_column=Column(CHAR(16), primary_key=True, nullable=False)
    )
    video_id: Optional[int] = Field(foreign_key="posts.id")
    hash_value: str = Field(max_length=255)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )