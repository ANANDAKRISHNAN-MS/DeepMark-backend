import piexif
import io
import tempfile
import os
import json
from fastapi import UploadFile
from PIL import Image
from PIL.ExifTags import TAGS
from starlette.datastructures import UploadFile as StarletteUploadFile, Headers

async def get_metadata(image_file: UploadFile) -> dict:
    # Read the image data
    content = await image_file.read()
    image = Image.open(io.BytesIO(content))
    
    # Reset file cursor for future operations
    await image_file.seek(0)
    
    # Initialize metadata dictionary
    metadata = {
        "filename": image_file.filename,
        "format": image.format,
        "size": image.size,
        "mode": image.mode
    }
    
    exif_data = {}
    custom_data = {}
    
    if hasattr(image, '_getexif') and image._getexif():
        exif = image._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                
                # Special handling for UserComment - this is where we'll store our custom data
                if tag == "UserComment" and isinstance(value, bytes):
                    try:
                        # Try to decode the UserComment
                        if value.startswith(b'ASCII\x00\x00\x00'):
                            # Remove ASCII prefix
                            decoded = value[8:].decode('utf-8').strip()
                        else:
                            decoded = value.decode('utf-8').strip()
                            
                        # Check if it's our custom deepmark data
                        if decoded.startswith('{') and '"deepmark":' in decoded:
                            custom_data = json.loads(decoded)
                            # Add it to a special deepmark section
                            metadata["deepmark"] = custom_data.get("deepmark", {})
                            continue
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        pass
                if tag == "MakerNote" : continue
                exif_data[tag] = str(value)  # Convert other values to string
    
    metadata["exif"] = exif_data
    return metadata

async def add_metadata(image_file: UploadFile, tags: dict) -> UploadFile:

    # Read the image data
    content = await image_file.read()
    
    # Reset file cursor
    await image_file.seek(0)
    
    # Create a temporary file to work with
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Load existing exif data
        try:
            exif_dict = piexif.load(temp_path)
        except:
            # If no EXIF data exists, create empty EXIF dict
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        
        # Structure the data with 'deepmark' as the top-level key
        deepmark_data = {
            "deepmark": tags
        }
        
        # Convert the structured data to a JSON string
        tags_str = json.dumps(deepmark_data, ensure_ascii=False)
        
        # Create ASCII/ASCII prefix for EXIF UserComment (needed for proper encoding)
        ascii_prefix = b'ASCII\x00\x00\x00'
        user_comment = ascii_prefix + tags_str.encode('utf-8')
        
        # 0x9286 is the tag for UserComment in Exif
        if "Exif" not in exif_dict:
            exif_dict["Exif"] = {}
        exif_dict["Exif"][0x9286] = user_comment
        
        # Convert the dictionary to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Insert the modified exif data into the image
        piexif.insert(exif_bytes, temp_path)
        
        # Read the modified image
        with open(temp_path, "rb") as f:
            modified_image = f.read()
        
        # Create a new file-like object with the modified image
        file_object = io.BytesIO(modified_image)
        
        # Get original filename or use default
        filename = image_file.filename or "modified_image.jpg"
        content_type = image_file.content_type or "image/jpeg"
        
        # Create a new UploadFile with the modified image
        modified_upload_file = StarletteUploadFile(
                file=file_object,
                filename=filename,
                headers=Headers({"content-type": content_type})
            )
        # Replace the file with our BytesIO object
        modified_upload_file.file = file_object
        
        return modified_upload_file
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)