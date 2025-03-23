
from fastapi import APIRouter, UploadFile, File

from hashing import Hash
from encryption import Encrypt,Decrypt
from video_module import metadata as VideoMetadata,watermark,analyze
from image_module import metadata as ImageMetadata
from services import upload

router = APIRouter(
    tags=["demo uploads"]
)

@router.post('/image-demo')
async def demo(media: UploadFile = File(...)):
    bmeta = await ImageMetadata.get_metadata(media)
    return {
        "bmetadata":bmeta,
    }

@router.post('/video-demo-watermark')
async def demo(media: UploadFile = File(...)):
    bmeta = await watermark.extract_watermark(media)
    return {
        "bmetadata":bmeta,
    }

@router.post('/video-demo-metadata')
async def demo(media: UploadFile = File(...)):
    bmeta = await VideoMetadata.get_metadata(media)
    return {
        "bmetadata":bmeta,
    }

@router.post('/video-cloudinary')
async def video_demo(media: UploadFile = File(...)):
   new_media = await VideoMetadata.append_metadata(media,{
        "copyright":f'deepmark'                                 
    })
   await upload.upload_file("demo","deepamrk",new_media)

@router.post('/image-cloudinary')
async def image_demo(media: UploadFile = File(...)):
   new_media = await ImageMetadata.add_metadata(media,{
        "copyright":f'deepamrksncsnjsnvosnvosnvosnnvksnvlksnvlknlksnc'                                 
    })
   await upload.upload_file("demo","deepamrksncsnjsnvosnvosnvosnnvksnvlksnvlknlksnc",new_media)

@router.post('/video-analyze')
async def demo(media: UploadFile = File(...)):
    hash = await analyze.analyze_video_face_recognition(media)
    return hash