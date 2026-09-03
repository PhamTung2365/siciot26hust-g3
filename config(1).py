"""
Smart Lock Configuration
- Model settings
- Database paths
- Server settings
"""

import os

# ==================== PATHS ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACES_DB_DIR = os.path.join(BASE_DIR, 'faces_db')
CAPTURES_DIR = os.path.join(BASE_DIR, 'captures')

# ==================== MODEL ====================
# InsightFace model
MODEL_NAME = 'buffalo_l'  # buffalo_l, buffalo_m, buffalo_s
DETECTION_SIZE = (320, 320)  # (height, width) - higher = more accurate but slower
RECOGNITION_THRESHOLD = 0.80  # Threshold for face match (0.0-1.0)

# Context: -1 = CPU, 0+ = GPU device ID
MODEL_CONTEXT = -1

# ==================== CAMERA ====================
CAMERA_DEVICE_ID = 0  # 0 = default camera, 1+ = other cameras
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# ==================== VIDEO STREAM ====================
VIDEO_QUALITY = 85  # JPEG quality (0-100)
VIDEO_FPS_DISPLAY_INTERVAL = 30  # Update FPS counter every N frames
VIDEO_SHOW_LANDMARKS = True  # Show 5-point landmarks

# ==================== SERVER ====================
SERVER_HOST = '0.0.0.0'  # 0.0.0.0 = all interfaces
SERVER_PORT = 5000
SERVER_DEBUG = False  # Set to True only for development
SERVER_THREADED = True

# ==================== AUTO CREATE DIRECTORIES ====================
for directory in [FACES_DB_DIR, CAPTURES_DIR]:
    os.makedirs(directory, exist_ok=True)
