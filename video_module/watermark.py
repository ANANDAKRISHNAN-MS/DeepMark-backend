import cv2
import numpy as np
import pywt
import os
import tempfile
from collections import Counter
from fastapi import UploadFile
from io import BytesIO
from tqdm import tqdm
from starlette.datastructures import UploadFile as StarletteUploadFile

async def embed_watermark(video_file: UploadFile, watermark_text: str) -> UploadFile:
    """
    Embeds a watermark in the given UploadFile video and returns a new UploadFile.
    """
    video_bytes = BytesIO(await video_file.read())
    video_format = os.path.splitext(video_file.filename)[1]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=video_format) as temp_input:
        temp_input.write(video_bytes.getvalue())
        temp_input_path = temp_input.name
    
    cap = cv2.VideoCapture(temp_input_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=video_format) as temp_output:
        temp_output_path = temp_output.name
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output_path, fourcc, fps, (frame_width, frame_height))
    
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    with tqdm(total=frame_count, desc="🎬 Watermarking video", unit=" frames") as pbar:
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % 15 == 0:
                frame = await embed_frame_watermark(frame, watermark_text)
            
            out.write(frame)
            pbar.update(1)
            frame_idx += 1
    
    cap.release()
    out.release()
    os.remove(temp_input_path)
    
    with open(temp_output_path, "rb") as f:
        output_bytes = BytesIO(f.read())
    os.remove(temp_output_path)
   
    video_file.file.seek(0)
    output_upload = StarletteUploadFile(
                file=output_bytes,
                filename=f"output{video_format}",
    )

    return output_upload

async def embed_frame_watermark(frame, watermark_text):
    yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
    y_channel = yuv[:,:,0].astype(float)
    
    coeffs = pywt.dwt2(y_channel, 'haar')
    LL1, (LH1, HL1, HH1) = coeffs
    coeffs2 = pywt.dwt2(LL1, 'haar')
    LL2, (LH2, HL2, HH2) = coeffs2
    
    watermark_bits = ''.join(format(ord(c), '08b') for c in watermark_text if ord(c) <= 255)
    
    rows, cols = LL2.shape
    required_pixels = len(watermark_bits)
    if rows * cols < required_pixels:
        return frame
    
    alpha = 1.0
    for i, bit in enumerate(watermark_bits):
        row, col = 4 + (i // 32), 4 + (i % 32)
        if row < LL2.shape[0] and col < LL2.shape[1]:
            original_value = LL2[row, col]
            LL2[row, col] = original_value + alpha * abs(original_value) if bit == '1' else original_value - alpha * abs(original_value)
    
    LL1_modified = pywt.idwt2((LL2, (LH2, HL2, HH2)), 'haar')
    LL1_modified = cv2.resize(LL1_modified, (LL1.shape[1], LL1.shape[0])) if LL1_modified.shape != LL1.shape else LL1_modified
    
    y_channel_modified = pywt.idwt2((LL1_modified, (LH1, HL1, HH1)), 'haar')
    y_channel_modified = cv2.resize(y_channel_modified, (y_channel.shape[1], y_channel.shape[0])) if y_channel_modified.shape != y_channel.shape else y_channel_modified
    
    yuv[:,:,0] = np.clip(y_channel_modified, 0, 255).astype(np.uint8)
    return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

async def extract_watermark(video_file: UploadFile):
    """
    Extracts the watermark from an UploadFile video.
    """
    video_bytes = BytesIO(await video_file.read())
    video_file.file.seek(0)
    video_format = os.path.splitext(video_file.filename)[1]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=video_format) as temp_input:
        temp_input.write(video_bytes.getvalue())
        temp_input_path = temp_input.name
    
    cap = cv2.VideoCapture(temp_input_path)
    extracted_watermarks = []
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    with tqdm(total=frame_count, desc="🔍 Extracting watermark", unit=" frames") as pbar:
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % 15 == 0:
                watermark = await extract_frame_watermark(frame)
                if watermark and len(watermark) > 8:
                    extracted_watermarks.append(watermark[:16])
            
            pbar.update(1)
            frame_idx += 1
    
    cap.release()
    os.remove(temp_input_path)
    video_file.file.seek(0)
    
    # Return the most common watermark found
    if extracted_watermarks:
        if len(extracted_watermarks) <=2 : return None

        watermark_counts = Counter(extracted_watermarks)

        most_common = watermark_counts.most_common(1)
        return most_common[0][0] if most_common and most_common[0][1] >= 2 else None
    
    # return set(extracted_watermarks)

async def extract_frame_watermark(frame):
    yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
    y_channel = yuv[:,:,0].astype(float)
    
    coeffs = pywt.dwt2(y_channel, 'haar')
    LL1, (LH1, HL1, HH1) = coeffs
    coeffs2 = pywt.dwt2(LL1, 'haar')
    LL2, (LH2, HL2, HH2) = coeffs2
    
    if np.std(LL2) < 0.5:
        return None
    
    binary_mask = cv2.adaptiveThreshold(
        LL2.astype(np.uint8),
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    
    watermark_bits = ''.join('1' if binary_mask[row, col] > 0 else '0' for row in range(4, 20) for col in range(4, 36) if row < binary_mask.shape[0] and col < binary_mask.shape[1])
    
    watermark = ''.join(chr(int(watermark_bits[i:i+8], 2)) for i in range(0, len(watermark_bits), 8) if 32 <= int(watermark_bits[i:i+8], 2) <= 126)
    
    return watermark if watermark else None


# if __name__ == "__main__":
#     video_path = "./video_module/demo_analyze.MOV"
#     test_watermark = "nandu09112003nan"
#     print(f"Embedding watermark: {test_watermark}")
#     embed_watermark(video_path, test_watermark)
#     extracted = extract_watermark(video_path)
#     print(f"Extracted watermark: {extracted}")