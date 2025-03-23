from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt,JWTError
from datetime import datetime,timedelta
from sqlmodel import select

from dependencies.db import SessionDep
from models import security,schemas


oauth2_bearer = OAuth2PasswordBearer(tokenUrl="v1/auth/token")
SECRET_KEY = security.jwtsettings.secret_key
ALGORITHM = security.jwtsettings.algorithm
TOKEN_EXPIRE_MINS = security.jwtsettings.token_expire_mins
 
#create access token
async def create_access_token(username: str, id: str):
    encode = {"sub" : username, "id" : id}
    expires = datetime.utcnow() + timedelta(minutes=int(TOKEN_EXPIRE_MINS))
    encode.update({"exp" : expires})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)


#get current user from token
async def get_current_user(db: SessionDep, token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username : str = payload.get("sub")
        id : str = payload.get("id")
        expires : datetime = payload.get("exp")
        if datetime.fromtimestamp(expires) < datetime.now():
            return None, "token expired"
        if username is None or id is None:
            return None, "invalid token"
        result = await db.execute(select(schemas.User).where(schemas.User.user_id == id))
        db_user = result.scalar_one_or_none()
        if not db_user:
           return None,"'user does not exist anymore"
        if db_user.warning == 3:
           return None,"'user can't access account, limit reached" 
        return db_user, ""
    except JWTError:
        print("jwt error")
        return None,"error"
    
async def verify_token(db: SessionDep, token: str):
    user, detail = await get_current_user(db, token)
    if not user: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user