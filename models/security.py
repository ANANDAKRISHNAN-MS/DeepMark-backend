from pydantic_settings import BaseSettings

#Classes to Access Environment Variables

class Master(BaseSettings):
    master_key: str   
    class Config:
        env_file = ".env"
        extra = "ignore"

class Database(BaseSettings):
    pg_host : str
    pg_port : str
    pg_database : str
    pg_user : str
    pg_password : str
    class Config:
        env_file = ".env"
        extra = "ignore"
    
class JWT(BaseSettings):
    secret_key : str
    algorithm : str
    token_expire_mins : str
    
    class Config:
        env_file = ".env"
        extra = "ignore"

class CLOUDINARY(BaseSettings):
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret_key: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"

master = Master()
database = Database()
jwtsettings = JWT()
cloudinary_settings = CLOUDINARY()



