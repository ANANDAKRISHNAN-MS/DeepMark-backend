import cloudinary.uploader
import uuid  
import os
from fastapi import File, UploadFile, HTTPException

from dependencies import cloud

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"}

async def upload_file(username: str, metadata_value: str, file: UploadFile = File(...)):
    try:
       
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension in IMAGE_EXTENSIONS:
            resource_type = "image"
        elif file_extension in VIDEO_EXTENSIONS:
            resource_type = "video"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        new_filename = f"{uuid.uuid4()}"

        result = cloudinary.uploader.upload(
            file.file.read(),
            folder=f'deepmark/{username}',
            resource_type=resource_type,  
            public_id=new_filename,  
            overwrite=True,
            context={
                "copyright":f'deepmark{metadata_value}'
            }    
        )

        return  result["public_id"].split("/")[-1]  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def delete_file(username:str, public_id: str, resource_type: str):
    try:
        corrected_public_id = f'deepmark/{username}/{public_id}'
        result = cloudinary.uploader.destroy(
            corrected_public_id,
            resource_type=resource_type
        )

        if result.get("result") != "ok":
            raise HTTPException(status_code=404, detail="File not found or already deleted")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))