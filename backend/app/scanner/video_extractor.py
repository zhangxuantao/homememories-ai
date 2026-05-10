# backend/app/scanner/video_extractor.py
import os
import cv2
import numpy as np


def extract_video_info(filepath: str) -> dict:
    """Extract duration, width, height from video file using OpenCV.

    Returns dict with keys: duration, width, height, fps.
    All values are None if the file can't be opened.
    """
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return {"duration": None, "width": None, "height": None, "fps": None}

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    duration = None
    if fps and fps > 0 and frame_count and frame_count > 0:
        duration = frame_count / fps

    cap.release()
    return {"duration": round(duration, 1) if duration else None, "width": width, "height": height, "fps": fps}


def extract_keyframe(filepath: str, position_ratio: float = 0.25) -> np.ndarray | None:
    """Extract a single frame from video at given position (0.0 to 1.0).

    Returns the frame as a BGR numpy array, or None on failure.
    """
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return None

    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if not frame_count or frame_count <= 0:
        cap.release()
        return None

    target_frame = int(frame_count * position_ratio)
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        return None
    return frame


def generate_video_thumbnail(filepath: str, thumb_dir: str, source_root: str, size: int = 300) -> str | None:
    """Generate a thumbnail for a video file.

    Extracts a keyframe, resizes to thumbnail size, saves as JPEG.
    Returns the thumbnail path relative to source_root, or None on failure.
    """
    frame = extract_keyframe(filepath)
    if frame is None:
        return None

    # Resize maintaining aspect ratio, then center-crop to square
    h, w = frame.shape[:2]
    if h <= 0 or w <= 0:
        return None

    # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    from PIL import Image

    img = Image.fromarray(frame_rgb)
    img.thumbnail((size, size))

    rel_path = os.path.relpath(filepath, source_root)
    thumb_path = os.path.join(thumb_dir, rel_path + ".jpg")
    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
    img.save(thumb_path, "JPEG", quality=80)
    return thumb_path
