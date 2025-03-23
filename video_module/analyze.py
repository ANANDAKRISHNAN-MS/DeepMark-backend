import imageio
import face_recognition
import json
import sys
import cv2
from tqdm import tqdm
from fastapi import UploadFile
from io import BytesIO

from hashing import Hash

async def normalize_orientation(frame):
    if frame.shape[0] > frame.shape[1]:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame


async def analyze_video_face_recognition(video_file: UploadFile, frame_skip=5):
    """
    Analyzes faces in an uploaded video using imageio instead of temporary files.
    
    Args:
        video_file (UploadFile): Video file uploaded through FastAPI
        frame_skip (int): Number of frames to skip between processing
    
    Returns:
        str: SHA256 hash of the facial recognition data
    """
    try:
        # Read video bytes into memory
        video_bytes = BytesIO(await video_file.read())
        video_file.file.seek(0)
        video_format = video_file.filename.split('.')[-1] if video_file.filename else 'mp4'

        # Read video with imageio
        with imageio.get_reader(video_bytes, format=video_format) as reader:
            total_frames = reader.count_frames()
            results = []
            
            # Disable tqdm if running in a non-terminal environment
            disable_tqdm = not sys.stdout.isatty()
            
            with tqdm(
                total=total_frames,
                desc="📽️ Analyzing Video",
                unit=" frames",
                colour="blue",
                disable=disable_tqdm
            ) as pbar:
                for frame_count, frame in enumerate(reader):
                    pbar.update(1)  # Update progress bar
                    
                    if frame_count % frame_skip != 0:
                        continue
                    
                    rgb_frame = await normalize_orientation(frame)
                    face_locations = face_recognition.face_locations(rgb_frame)
                    face_landmarks = face_recognition.face_landmarks(rgb_frame)
                    
                    frame_data = {"frame": frame_count, "faces": []}
                    
                    for i, face_location in enumerate(face_locations):
                        top, right, bottom, left = face_location
                        landmarks = face_landmarks[i] if i < len(face_landmarks) else {}
                        frame_data["faces"].append({
                            "rect": {"top": top, "right": right, "bottom": bottom, "left": left},
                            "landmarks": landmarks
                        })
                    
                    results.append(frame_data)

            # Convert results to JSON and hash
            json_string = json.dumps(results, sort_keys=True)
            hashed_data = await Hash.sha256(json_string)

            return hashed_data
    except Exception as e:
        raise Exception(f"Error processing video: {str(e)}")
    # finally:
    #     multiprocessing.resource_tracker._cleanup_semaphores() 
