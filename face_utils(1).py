"""
Face Detection & Embedding Module
- Load model once
- Extract face embeddings
- Use face_db for recognition logic
"""

from insightface.app import FaceAnalysis

from config import DETECTION_SIZE, MODEL_CONTEXT, MODEL_NAME

PROVIDERS = (['CUDAExecutionProvider', 'CPUExecutionProvider']
             if MODEL_CONTEXT >= 0 else ['CPUExecutionProvider'])

print(f"📥 Loading InsightFace model ({MODEL_NAME})...")
try:
    app = FaceAnalysis(name=MODEL_NAME, providers=PROVIDERS)
    app.prepare(ctx_id=MODEL_CONTEXT, det_size=DETECTION_SIZE)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Model load error: {e}")
    app = None


# ==================== FACE DETECTION ====================
def get_face_embedding(frame):
    """
    Extract face and embedding from frame
    Returns: (face_obj, embedding) or (None, None)
    """
    if app is None:
        return None, None

    try:
        faces = app.get(frame)

        if len(faces) == 0:
            return None, None

        face = faces[0]  # Get first face
        embedding = face.embedding  # numpy array (512,)

        return face, embedding

    except Exception as e:
        print(f"❌ Detection error: {e}")
        return None, None


# ==================== MODEL INFO ====================
def get_model_info():
    """Get model information"""
    if app is None:
        return {'status': 'error', 'message': 'Model not loaded'}

    return {
        'status': 'ok',
        'model': MODEL_NAME,
        'det_size': DETECTION_SIZE,
        'providers': PROVIDERS,
        'embedding_size': 512
    }
