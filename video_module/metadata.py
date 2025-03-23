import ffmpeg
import io
import tempfile
import os
from fastapi import UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile, Headers

async def get_metadata(upload_file: UploadFile):
    """Extract metadata from an uploaded video file using a temporary file."""
    
    # Create a temporary file with the same extension
    suffix = os.path.splitext(upload_file.filename)[-1] or ".mp4"  # Default to .mp4 if unknown
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(upload_file.file.read())  # Write uploaded file to temp
        temp_file_path = temp_file.name

    try:
        probe = ffmpeg.probe(temp_file_path)
        metadata = probe.get("format", {}).get("tags", {})
        format_name = probe.get("format", {}).get("format_name", "mp4")  # Default to mp4 if unknown
    except ffmpeg.Error as e:
        print(f"FFmpeg probe error: {e}")
        metadata, format_name = {}, "mp4"
    finally:
        os.remove(temp_file_path)  # Delete temp file immediately

    # Reset file pointer
    upload_file.file.seek(0)
    return metadata, format_name


async def append_metadata(upload_file: UploadFile, new_metadata) -> UploadFile:
    """Modify metadata using temporary files to ensure reliability."""
    
    # Get existing metadata
    existing_metadata, format_name = await get_metadata(upload_file)
    print(f"Existing Metadata: {existing_metadata}, Format: {format_name}")
    
    # Merge metadata
    merged_metadata = {
        k: str(v) for k, v in {**existing_metadata, **new_metadata}.items()
        if v and isinstance(v, (str, int, float)) and k.lower() != "encoder"
    }
    print("Merged Metadata:", merged_metadata)
    
    # Use first format if multiple are detected
    primary_format = format_name.split(",")[0].strip()
    
    # Create temporary input and output files
    temp_in_path = None
    temp_out_path = None
    
    try:
        # Create input temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{primary_format}") as temp_in:
            content = await upload_file.read()
            temp_in.write(content)
            temp_in_path = temp_in.name
        
        # Reset the file pointer
        await upload_file.seek(0)
        
        # Create output temp file with a unique name to avoid conflicts
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{primary_format}") as temp_out:
            temp_out_path = temp_out.name
        

        
        # Run FFmpeg with temporary files (more reliable than pipes)
        try:
            input_stream = ffmpeg.input(temp_in_path)
            output_stream = input_stream.output(
                temp_out_path, 
                vcodec='copy', 
                acodec='copy',
                **{f'metadata:g:{k}': f'{k}={v}' for k, v in merged_metadata.items()}
            )
            ffmpeg.run(output_stream, overwrite_output=True)
            
            # Read the output file
            with open(temp_out_path, 'rb') as f:
                output_content = f.read()
                
            # Create a new UploadFile
            output_file = io.BytesIO(output_content)
            output_upload = StarletteUploadFile(
                file=output_file,
                filename=f"updated_{upload_file.filename}",
                headers=Headers({"content-type": f"video/{primary_format}"})
            )
            
            return output_upload
            
        except ffmpeg.Error as e:
            print(f"FFmpeg error: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}")
            # If FFmpeg fails, return the original file
            return upload_file
    finally:
        # Clean up temporary files
        if temp_in_path and os.path.exists(temp_in_path):
            os.remove(temp_in_path)
        if temp_out_path and os.path.exists(temp_out_path):
            os.remove(temp_out_path)

        

