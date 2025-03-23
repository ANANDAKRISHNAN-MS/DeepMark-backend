import re
from fastapi import UploadFile,HTTPException,status
from sqlmodel import select
from typing import Optional

from dependencies.db import SessionDep
from models import schemas
from encryption import Decrypt,Encrypt
from video_module import analyze,metadata as VideoMetadata,watermark
from image_module import metadata as ImageMetadata
from hashing import Hash


#process media
async def process_media(db: SessionDep, media: UploadFile, user: schemas.User):
    if not media.content_type.startswith("video/") and not media.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="media is not an image or a video"
        )
    if media.content_type.startswith("image/"):
        return await process_image(db, media, user)
    else:
       return await process_video(db, media, user)

#process image media
async def process_image(db: SessionDep, media: UploadFile, user: schemas.User):
    metadata = await ImageMetadata.get_metadata(media)
    print(metadata)

#process video media   
async def process_video(db: SessionDep, media: UploadFile, user: schemas.User):
    # hashed_value = await analyze.analyze_video_face_recognition(media)
    hashed_value="24d52db5740495ee7ea0ab117a053b7f9fb887664d66c746183810eea94a6b2b"
    metadata = await VideoMetadata.get_metadata(media)
    await check_video_metadata(db, metadata, user, hashed_value)
    embeded_watermark = await watermark.extract_watermark(media)
    await check_video_watermark(db, embeded_watermark, user, hashed_value)
    return hashed_value
            

async def check_video_metadata(db:SessionDep, metadata:str, curr_user:schemas.User, hashed_value: str ):
    user_cipher = await Decrypt.generate_user_cipher(curr_user.security_key)
    copyright = metadata[0].get("copyright", None)
    if copyright and copyright.startswith("deepmark"):
        text = copyright[len("deepmark"):]
        parts = re.split(r'(=)', text)
        result = []
        for i in range(0, len(parts) - 1, 2):  
            result.append(parts[i] + parts[i + 1])
        if len(result) == 2 :
            dmm_id_user = await Decrypt.decrypt_data(result[0],user_cipher)
            if dmm_id_user is not None:
                result = await db.execute(
                    select(schemas.DMM).where(schemas.DMM.dmm_id == dmm_id_user)
                )
                post = result.scalar_one_or_none()
                if post:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="post was already uploaded"
                    )
            dmm_id_master = await Decrypt.decrypt_data(result[1],Decrypt.master_cipher)
            result = await db.execute(
                select(schemas.DMM, schemas.Post, schemas.User)
                .join(schemas.Post, schemas.DMM.video_id == schemas.Post.id)
                .join(schemas.User, schemas.User.user_id == schemas.Post.user_id)
                .where(schemas.DMM.dmm_id == dmm_id_master)
            )
            data = result.first()
            dmm, post, user = data
            detected_activity = schemas.Activity(
                receiver_name=user.username,
                sender_name=curr_user.username,
                media_type=post.media_type,
                detected_user_profile_picture=curr_user.profile_picture,
                detected_post_id=post.id,
                detected_post_url=post.media_url
            )
            db.add(detected_activity)
            if(dmm.hash_value != hashed_value):
                curr_user.warning+=1
                db.add(curr_user)
                await db.commit()
                await db.refresh(curr_user)
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f'you don\'t own this media, you have only {3-curr_user.warning} chance remaining'
                )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail=f'you don\'t own this media'
            )
            
async def check_video_watermark(
    db: SessionDep,
    embeded_watermark: Optional[str],
    curr_user: schemas.User,
    hashed_value: str
):
    if not embeded_watermark:
        return 
    
    if embeded_watermark == "video manipulated":
       raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="you don't own this media"
        )
    result = await db.execute(
                select(schemas.DMM, schemas.Post, schemas.User)
                .join(schemas.Post, schemas.DMM.video_id == schemas.Post.id)
                .join(schemas.User, schemas.User.user_id == schemas.Post.user_id)
                .where(schemas.DMM.dmm_id == embeded_watermark)
            )
    
    data = result.first()
    if not data :
       raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="you don't own this media"
        )
    
    dmm, post, user = data
    if post.user_id != curr_user.user_id:
        detected_activity = schemas.Activity(
                receiver_name=user.username,
                sender_name=curr_user.username,
                media_type=post.media_type,
                detected_user_profile_picture=curr_user.profile_picture,
                detected_post_id=post.id,
                detected_post_url=post.media_url
            )
        db.add(detected_activity)
        if(dmm.hash_value != hashed_value):
            curr_user.warning+=1
            db.add(curr_user)
            await db.commit()
            await db.refresh(curr_user)
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail=f'you don\'t own this media, you have only {3-curr_user.warning} chance remaining'
            )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="you don't own this media"
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="post was already uploaded"
    ) 
        
            
#add attributes
async def add_attributes(media: UploadFile, user: schemas.User) -> dict:
    if not media.content_type.startswith("video/") and not media.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="media is not an image or a video"
        )
    if media.content_type.startswith("image/"):
        return await add_image_attributes(media, user)
    else:
       return await add_video_attributes(media, user)
    
         
#add attributes to image
async def add_image_attributes(media: UploadFile, user: schemas.User) -> dict:
    user_cipher = await Decrypt.generate_user_cipher(user.security_key) 

    dmm_id = await Hash.uuid()
    metadata_value = await Encrypt.encrypt_data(dmm_id,user_cipher)
    metadata_value += await Encrypt.encrypt_data(dmm_id,Encrypt.master_cipher)
    metadata_added_media = await ImageMetadata.add_metadata(media,{
        "copyright":f's{metadata_value}'
    })
    return {
        "dmm_id": dmm_id,
        "metadata_value": metadata_value,
        "final_media": metadata_added_media
    }  


#add attributes to video
async def add_video_attributes(media: UploadFile, user: schemas.User) -> dict:
    user_cipher = await Decrypt.generate_user_cipher(user.security_key)

    dmm_id = await Hash.uuid()

    watermark_added_media = await watermark.embed_watermark(media, dmm_id)

    metadata_value = await Encrypt.encrypt_data(dmm_id,user_cipher)
    metadata_value += await Encrypt.encrypt_data(dmm_id,Encrypt.master_cipher)
    final_media = await VideoMetadata.append_metadata(watermark_added_media,{
        "copyright":f'deepmark{metadata_value}'
    })
    return {
        "dmm_id": dmm_id,
        "metadata_value":metadata_value,
        "final_media": final_media
    } 



    


