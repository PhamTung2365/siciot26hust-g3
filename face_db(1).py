"""
Face Database Module
- Load database once on startup
- Cache in memory
- Thread-safe operations
"""

import os
import pickle
import re
import threading
import time

import numpy as np
from config import FACES_DB_DIR, RECOGNITION_THRESHOLD

DB_DIR = FACES_DB_DIR
THRESHOLD = RECOGNITION_THRESHOLD

# Thread-safe cache
_db_lock = threading.RLock()
_faces_cache = {}
_cache_valid = False


def _person_path(name):
    """Return a safe database path for a display name."""
    if not isinstance(name, str) or name != name.strip():
        raise ValueError("Name must be a trimmed string")
    if name in {'.', '..'} or not re.fullmatch(r'[\w .-]{2,64}', name):
        raise ValueError("Name must be 2-64 letters, numbers, spaces, dots, _ or -")
    return os.path.join(DB_DIR, f"{name}.pkl")

# ==================== CACHE MANAGEMENT ====================
def _init_cache():
    """Load tất cả faces vào memory một lần"""
    global _faces_cache, _cache_valid

    with _db_lock:
        os.makedirs(DB_DIR, exist_ok=True)
        _faces_cache = {}

        for filename in os.listdir(DB_DIR):
            if filename.endswith('.pkl'):
                filepath = os.path.join(DB_DIR, filename)
                try:
                    with open(filepath, 'rb') as f:
                        data = pickle.load(f)
                        name = data.get('name', filename.replace('.pkl', ''))
                        embeddings = data.get('embeddings', [])
                        _faces_cache[name] = [np.array(e) for e in embeddings]
                        print(f"  ✓ {name}: {len(embeddings)} faces")
                except Exception as e:
                    print(f"  ✗ Error loading {filename}: {e}")

        _cache_valid = True
        print(f"✅ Cache initialized: {len(_faces_cache)} people")

def refresh_cache():
    """Reload the in-memory cache from disk."""
    global _cache_valid
    _cache_valid = False
    _init_cache()

def get_cache():
    """Get current cache (lazy load if needed)"""
    global _cache_valid

    if not _cache_valid:
        _init_cache()

    return _faces_cache.copy()

# ==================== SIMILARITY ====================
def cosine_similarity(a, b):
    """Cosine similarity between two vectors (-1 to 1)."""
    a = np.array(a).flatten()
    b = np.array(b).flatten()

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return np.dot(a, b) / (norm_a * norm_b)

# ==================== FACE OPERATIONS ====================
def add_face(name, embedding):
    """
    Add a new face embedding to database
    Returns: count of embeddings for this person
    """
    with _db_lock:
        os.makedirs(DB_DIR, exist_ok=True)
        filepath = _person_path(name)
        now = time.time()

        # Load existing or create new
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
        else:
            data = {
                'name': name,
                'embeddings': [],
                'created_at': now,
                'updated_at': now
            }

        # Add new embedding
        stored_embedding = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
        data['embeddings'].append(stored_embedding)
        data['updated_at'] = now

        # Save to disk
        temp_path = f"{filepath}.tmp"
        with open(temp_path, 'wb') as f:
            pickle.dump(data, f)
        os.replace(temp_path, filepath)

        # Update cache
        _faces_cache[name] = [np.array(e) for e in data['embeddings']]

        count = len(data['embeddings'])
        print(f"  ✓ {name}: {count} embeddings")
        return count

def recognize_face(embedding, threshold=THRESHOLD):
    """
    Recognize a face
    Returns: (name, confidence_score) or (None, best_score)
    """
    with _db_lock:
        cache = get_cache()

    if not cache:
        return None, 0.0

    best_name = None
    best_score = 0.0

    for name, embeddings in cache.items():
        for stored_emb in embeddings:
            score = cosine_similarity(embedding, stored_emb)
            if score > best_score:
                best_score = score
                best_name = name

    # Return only if above threshold
    return (best_name if best_score >= threshold else None), best_score

def delete_person(name):
    """Delete a person from database"""
    with _db_lock:
        filepath = _person_path(name)
        if os.path.exists(filepath):
            os.remove(filepath)
            if name in _faces_cache:
                del _faces_cache[name]
            print(f"  ✓ Deleted: {name}")
            return True
    return False

def get_person_count(name=None):
    """Get face count for person or total count"""
    with _db_lock:
        cache = get_cache()

    if name:
        return len(cache.get(name, []))
    return sum(len(embeddings) for embeddings in cache.values())

def get_all_names():
    """Get list of all registered people"""
    with _db_lock:
        cache = get_cache()
    return sorted(cache)

def get_all_people_with_counts():
    """Get all people with their face counts"""
    with _db_lock:
        cache = get_cache()

    return [
        {'name': name, 'count': len(embeddings)}
        for name, embeddings in sorted(cache.items())
    ]

# ==================== INIT ====================
# Initialize cache on module load
print("📁 Initializing face database...")
_init_cache()
