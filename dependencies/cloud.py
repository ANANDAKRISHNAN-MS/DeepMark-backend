import cloudinary

from models.security import cloudinary_settings

cloudinary.config(
    cloud_name=cloudinary_settings.cloudinary_cloud_name,
    api_key=cloudinary_settings.cloudinary_api_key,
    api_secret=cloudinary_settings.cloudinary_api_secret_key
)
    
    