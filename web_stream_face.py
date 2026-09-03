import os
import socket
import threading
import time

import cv2
from flask import Flask, Response, jsonify, redirect, render_template, request, url_for

from auth import (
    AuthError,
    admin_required,
    authenticate,
    change_password,
    create_user,
    csrf_token,
    csrf_protect,
    current_user,
    init_auth,
    list_users,
    login_required,
    sign_in,
    sign_out,
    validate_csrf,
)

# Import configuration
from config import (
    CAMERA_DEVICE_ID,
    CAMERA_FPS,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CAPTURES_DIR,
    SERVER_DEBUG,
    SERVER_HOST,
    SERVER_PORT,
    SERVER_THREADED,
    VIDEO_FPS_DISPLAY_INTERVAL,
    VIDEO_QUALITY,
    VIDEO_SHOW_LANDMARKS,
)

# Import modules
from face_db import (
    THRESHOLD,
    add_face,
    delete_person,
    get_all_names,
    get_all_people_with_counts,
    get_person_count,
    recognize_face,
)
from face_utils import get_face_embedding, get_model_info

# ==================== GLOBAL STATE ====================
class CameraState:
    def __init__(self):
        self.lock = threading.RLock()
        self.faces = 0
        self.fps = 60
        self.match = False
        self.name = ''
        self.confidence = 0.0
        self.frame_count = 0
        self.is_ready = False

state = CameraState()
camera_lock = threading.Lock()

# ==================== INIT FLASK ====================
app = Flask(__name__)
init_auth(app)

# ==================== CAMERA SETUP ====================
def init_camera():
    """Initialize camera with auto-detection"""
    print("\nSearching for camera...")
    candidates = [CAMERA_DEVICE_ID] + [i for i in range(7) if i != CAMERA_DEVICE_ID]
    for device_id in candidates:
        try:
            cap = cv2.VideoCapture(device_id)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"Camera found: /dev/video{device_id}")
                    print(f"Resolution: {frame.shape[1]}x{frame.shape[0]}")
                    return cap, device_id
            cap.release()
        except Exception as exc:
            print(f"Camera {device_id}: {exc}")

    print("No camera found!")
    return None, None

cap, device_id = init_camera()
if cap is None:
    print("Server will start without video; connect a camera and restart")


def read_frame():
    """Read one frame without racing other Flask request threads."""
    if cap is None:
        return False, None
    with camera_lock:
        return cap.read()


def timestamp():
    """Filename-safe timestamp with sub-second collision protection."""
    return f"{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1_000_000_000:09d}"

# ==================== VIDEO STREAM ====================
def generate_frames():
    """Generate video frames for MJPEG stream"""
    frame_count = 0
    fps = 0.0
    fps_start = time.time()

    while True:
        ret, frame = read_frame()
        if not ret:
            print("Camera disconnected")
            with state.lock:
                state.is_ready = False
            break

        frame_count += 1

        # Calculate FPS every 30 frames
        if frame_count % VIDEO_FPS_DISPLAY_INTERVAL == 0:
            elapsed = time.time() - fps_start
            fps = VIDEO_FPS_DISPLAY_INTERVAL / elapsed if elapsed > 0 else 0
            fps_start = time.time()

        # ========== PROCESS FRAME ==========
        face, embedding = get_face_embedding(frame)

        with state.lock:
            state.fps = round(fps, 1)
            state.faces = 1 if face is not None else 0
            state.frame_count = frame_count
            state.is_ready = get_model_info()['status'] == 'ok'

        # If face detected
        if face is not None and embedding is not None:
            bbox = face.bbox.astype(int)
            det_score = float(face.det_score)

            # Draw bounding box
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]),
                         (0, 255, 0), 2)

            # Draw detection confidence
            cv2.putText(frame, f"Det: {det_score:.2f}",
                       (bbox[0], bbox[1]-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Draw the model's five keypoints
            if VIDEO_SHOW_LANDMARKS and face.kps is not None:
                for point in face.kps:
                    x, y = int(point[0]), int(point[1])
                    cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)

            # ========== RECOGNITION ==========
            name, confidence = recognize_face(embedding)

            with state.lock:
                state.match = (name is not None and confidence >= THRESHOLD)
                state.name = name if name else 'Unknown'
                state.confidence = confidence if confidence else 0.0

            # Draw result
            if name and confidence >= THRESHOLD:
                text = f"{name} ({confidence*100:.1f}%)"
                color = (0, 255, 0)  # Green
            else:
                text = f"Unknown ({confidence*100:.1f}%))"
                color = (0, 0, 255)  # Red

            cv2.putText(frame, text,
                       (bbox[0], bbox[3]+25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        else:
            with state.lock:
                state.match = False
                state.name = ''
                state.confidence = 0.0

        # Draw info on frame
        with state.lock:
            cv2.putText(frame, f"Faces: {state.faces}",
                       (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"FPS: {state.fps:.1f}",
                       (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(frame, f"Threshold: {THRESHOLD*100:.0f}%",
                       (10, 85),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame,
                                  [cv2.IMWRITE_JPEG_QUALITY, VIDEO_QUALITY])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        # Yield frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame_bytes + b'\r\n')

# ==================== ROUTES ====================

@app.route('/')
@login_required
def index():
    """Home page"""
    user = current_user()
    all_people = get_all_people_with_counts()
    people_list = [p['name'] for p in all_people]
    face_counts = {p['name']: p['count'] for p in all_people}

    return render_template(
        'dashboard.html',
        people_list=people_list,
        face_counts=face_counts,
        people_count=len(people_list),
        total_count=get_person_count(),
        threshold=THRESHOLD,
        is_admin=user['role'] == 'admin',
        username=user['username'],
        user=user,
        csrf_token=csrf_token(),
    )

@app.route('/video_feed')
@login_required
def video_feed():
    """MJPEG stream endpoint"""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/status')
@login_required
def get_status():
    """Get current system status (called every 500ms)"""
    with state.lock:
        return jsonify({
            'ready': state.is_ready,
            'faces': state.faces,
            'fps': state.fps,
            'match': state.match,
            'name': state.name,
            'confidence': round(state.confidence, 3),
            'people_count': len(get_all_names()),
            'total_count': get_person_count()
        })


@app.route('/enroll_web', methods=['POST'])
@admin_required
@csrf_protect
def enroll_web():
    """Enroll a face from current frame"""
    try:
        data = request.get_json(silent=True) or {}
        name = data.get('name', '').strip()

        if not name:
            return jsonify({'status': 'error', 'message': 'Name is required'}), 400

        if len(name) < 2:
            return jsonify({'status': 'error', 'message': 'Name too short'}), 400

        print(f"\nEnrolling: {name}")

        # Get current frame
        ret, frame = read_frame()
        if not ret:
            return jsonify({'status': 'error', 'message': 'Camera error'}), 503

        # Extract face
        face, embedding = get_face_embedding(frame)

        if face is None:
            # Save debug image
            debug_path = os.path.join(CAPTURES_DIR, f"debug_no_face_{timestamp()}.jpg")
            cv2.imwrite(debug_path, frame)
            print(f"No face detected (saved debug: {debug_path})")
            return jsonify({
                'status': 'error',
                'message': 'No face detected. Look at camera and stay centered.'
            }), 422

        if embedding is None:
            return jsonify({'status': 'error', 'message': 'Embedding error'}), 500

        # Save to database
        count = add_face(name, embedding)

        print(f"  ✓ Enrolled {name} (total: {count} embeddings)")

        return jsonify({
            'status': 'success',
            'message': f'Enrolled: {name}',
            'count': count,
            'people_count': len(get_all_names()),
            'total_count': get_person_count()
        })

    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        print(f"Enroll error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/delete_person', methods=['POST'])
@admin_required
@csrf_protect
def delete_person_api():
    """Delete a registered person"""
    try:
        data = request.get_json(silent=True) or {}
        name = data.get('name', '').strip()

        if not name:
            return jsonify({'status': 'error', 'message': 'Name required'}), 400

        print(f"\nDeleting: {name}")

        if delete_person(name):
            print(f"  ✓ Deleted: {name}")

            return jsonify({
                'status': 'success',
                'message': f'Deleted: {name}',
                'people_count': len(get_all_names()),
                'total_count': get_person_count()
            })
        else:
            return jsonify({'status': 'error', 'message': 'Not found'}), 404

    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        print(f"Delete error: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/get_people')
@admin_required
def get_people():
    """Get all registered people with face counts"""
    return jsonify({
        'people': get_all_people_with_counts()
    })

@app.route('/capture', methods=['POST'])
@admin_required
@csrf_protect
def capture_image():
    """Capture current frame"""
    try:
        ret, frame = read_frame()
        if not ret:
            return jsonify({'status': 'error', 'message': 'Camera error'}), 503

        filename = f"capture_{timestamp()}.jpg"
        if not cv2.imwrite(os.path.join(CAPTURES_DIR, filename), frame):
            return jsonify({'status': 'error', 'message': 'Failed to save image'}), 500

        return jsonify({'status': 'success', 'filename': filename})

    except Exception as e:
        print(f"Capture error: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/info')
@login_required
def get_info():
    """Get system information"""
    return jsonify({
        'model': get_model_info(),
        'camera': device_id,
        'threshold': THRESHOLD,
        'people': len(get_all_names()),
        'total_faces': get_person_count()
    })


def _json_data():
    if not validate_csrf(request.headers.get('X-CSRF-Token')):
        return None, (jsonify({'status': 'error', 'message': 'Invalid CSRF token'}), 400)
    return request.get_json(silent=True) or {}, None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user():
        return redirect(url_for('index'))
    if request.method == 'POST':
        if not validate_csrf(request.form.get('csrf_token')):
            return render_template('login.html', error='Invalid request. Refresh and try again.', csrf_token=csrf_token()), 400
        user = authenticate(request.form.get('username', ''), request.form.get('password', ''))
        if user:
            sign_in(user)
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid username or password.', csrf_token=csrf_token()), 401
    return render_template('login.html', error='', csrf_token=csrf_token())


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    if not validate_csrf(request.form.get('csrf_token')):
        return jsonify({'status': 'error', 'message': 'Invalid CSRF token'}), 400
    sign_out()
    return redirect(url_for('login'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password_page():
    error = ''
    success = ''
    if request.method == 'POST':
        if not validate_csrf(request.form.get('csrf_token')):
            error = 'Invalid request. Refresh and try again.'
        elif request.form.get('new_password') != request.form.get('confirm_password'):
            error = 'New passwords do not match.'
        else:
            try:
                change_password(current_user()['username'], request.form.get('current_password', ''), request.form.get('new_password', ''))
                success = 'Password changed.'
            except AuthError as exc:
                error = str(exc)
    return render_template(
        'change_password.html', error=error, success=success,
        csrf_token=csrf_token(), username=current_user()['username'],
        user=current_user()
    )


@app.route('/admin/users')
@admin_required
def admin_users_page():
    return render_template(
        'admin_users.html', users=list_users(), csrf_token=csrf_token(),
        username=current_user()['username'], user=current_user()
    )


@app.route('/api/admin/users', methods=['GET', 'POST'])
@admin_required
def admin_users_api():
    if request.method == 'GET':
        return jsonify({'users': list_users()})
    data, error = _json_data()
    if error:
        return error
    try:
        user = create_user(data.get('username', ''), data.get('password', ''))
        return jsonify({'status': 'success', 'user': user}), 201
    except AuthError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400

# ==================== HTML UI ====================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Smart Lock - Face Recognition</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
        }
        .container {
            background: rgba(22, 33, 62, 0.95);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.9);
            max-width: 1000px;
            width: 100%;
            border: 1px solid #2a3a6a;
        }
        h1 {
            text-align: center;
            font-size: 28px;
            margin-bottom: 5px;
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 20px;
            font-size: 13px;
        }
        .subtitle span { color: #00ff88; font-weight: bold; }
        .video-box {
            background: #0f0f23;
            border-radius: 12px;
            overflow: hidden;
            border: 2px solid #2a3a6a;
            margin-bottom: 15px;
        }
        #video-stream {
            width: 100%;
            display: block;
            background: #000;
        }
        .status-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            padding: 15px;
            background: linear-gradient(135deg, rgba(42,58,106,0.6), rgba(10,10,26,0.6));
            border-radius: 10px;
            margin-bottom: 15px;
        }
        .status-item {
            text-align: center;
            padding: 8px;
        }
        .status-item .label {
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-item .value {
            font-size: 18px;
            font-weight: bold;
            color: #00d2ff;
            margin-top: 4px;
        }
        .status-item.active .value { color: #00ff88; }
        .status-item.error .value { color: #ff4444; }
        .status-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 6px;
        }
        .status-dot.on { background: #00ff88; box-shadow: 0 0 8px #00ff88; }
        .status-dot.off { background: #555; }
        .section {
            margin-bottom: 15px;
        }
        .section-title {
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            padding-bottom: 6px;
            border-bottom: 1px solid #2a3a6a;
        }
        .controls {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }
        .enroll-group {
            display: flex;
            gap: 8px;
            flex: 1;
            min-width: 250px;
        }
        .enroll-group input {
            flex: 1;
            min-width: 100px;
            padding: 8px 12px;
            border: 1px solid #2a3a6a;
            border-radius: 6px;
            background: #1a1a2e;
            color: white;
            font-size: 13px;
            outline: none;
        }
        .enroll-group input:focus {
            border-color: #3a7bd5;
            box-shadow: 0 0 8px rgba(58, 123, 213, 0.3);
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
            white-space: nowrap;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .btn:hover { transform: translateY(-1px); }
        .btn-primary { background: #3a7bd5; color: white; }
        .btn-primary:hover { background: #4a8be5; box-shadow: 0 4px 12px rgba(58, 123, 213, 0.4); }
        .btn-success { background: #00c853; color: white; }
        .btn-success:hover { background: #00e676; box-shadow: 0 4px 12px rgba(0, 200, 83, 0.4); }
        .btn-danger { background: #d32f2f; color: white; }
        .btn-danger:hover { background: #f44336; box-shadow: 0 4px 12px rgba(211, 47, 47, 0.4); }
        .btn-sm { padding: 6px 10px; font-size: 11px; }
        .people-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 8px;
        }
        .person-card {
            background: rgba(42, 58, 106, 0.5);
            border: 1px solid #2a3a6a;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            transition: all 0.2s;
        }
        .person-card:hover {
            background: rgba(58, 123, 213, 0.3);
            border-color: #3a7bd5;
            transform: translateY(-1px);
        }
        .person-card .name {
            font-weight: 600;
            color: #00d2ff;
            font-size: 12px;
            margin-bottom: 4px;
            word-break: break-word;
        }
        .person-card .count {
            font-size: 11px;
            color: #888;
            margin-bottom: 6px;
        }
        .person-card .count .num { color: #00ff88; font-weight: bold; }
        .person-card .del {
            background: #d32f2f;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 10px;
            cursor: pointer;
            width: 100%;
            transition: all 0.2s;
        }
        .person-card .del:hover { background: #f44336; }
        .log-box {
            background: #0a0a1a;
            border: 1px solid #2a3a6a;
            border-radius: 8px;
            padding: 10px;
            max-height: 100px;
            overflow-y: auto;
            font-size: 11px;
            font-family: 'Courier New', monospace;
            color: #888;
        }
        .log-entry {
            padding: 2px 0;
            border-bottom: 1px solid #111;
        }
        .log-entry:last-child { border-bottom: none; }
        .log-entry.ok { color: #00ff88; }
        .log-entry.err { color: #ff4444; }
        .log-entry.info { color: #ffaa00; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2a3a6a; border-radius: 3px; }
        @media (max-width: 640px) {
            .container { padding: 15px; }
            .status-bar { grid-template-columns: repeat(2, 1fr); }
            .controls { flex-direction: column; }
            .enroll-group { flex-direction: column; }
            .people-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>SMART LOCK</h1>
        <div class="subtitle">{{ username }}{% if is_admin %} · Administrator{% endif %} · <a href="{{ url_for('change_password_page') }}" style="color:#00d2ff">Change password</a>{% if is_admin %} · <a href="{{ url_for('admin_users_page') }}" style="color:#00d2ff">Manage users</a>{% endif %}</div>
        <form action="{{ url_for('logout') }}" method="post" style="text-align:center;margin:0 0 16px"><input type="hidden" name="csrf_token" value="{{ csrf_token }}"><button class="btn btn-danger btn-sm">Sign out</button></form>

        <!-- Video Stream -->
        <div class="video-box">
            <img id="video-stream" src="{{ url_for('video_feed') }}" alt="Stream">
        </div>

        <!-- Status Bar -->
        <div class="status-bar">
            <div class="status-item">
                <div class="label">Status</div>
                <div class="value">
                    <span class="status-dot" id="status-dot"></span>
                    <span id="status-text">Init...</span>
                </div>
            </div>
            <div class="status-item">
                <div class="label">Faces</div>
                <div class="value" id="face-count">0</div>
            </div>
            <div class="status-item">
                <div class="label">FPS</div>
                <div class="value" id="fps-val">0</div>
            </div>
            <div class="status-item">
                <div class="label">People</div>
                <div class="value" id="people-count">{{ people_count }}</div>
            </div>
            <div class="status-item">
                <div class="label">Total</div>
                <div class="value" id="total-count">{{ total_count }}</div>
            </div>
        </div>

        {% if is_admin %}
        <!-- Enroll Section -->
        <div class="section">
            <div class="section-title">Enroll</div>
            <div class="controls">
                <div class="enroll-group">
                    <input type="text" id="enroll-name" placeholder="Enter name..."
                           onkeypress="if(event.key==='Enter') enrollFace()">
                    <button class="btn btn-success" onclick="enrollFace()">📝 Enroll</button>
                </div>
                <button class="btn btn-primary" onclick="captureImage()">📸 Capture</button>
                <button class="btn btn-danger" onclick="clearLog()">🗑️ Clear</button>
            </div>
        </div>

        <!-- People Section -->
        <div class="section">
            <div class="section-title">Registered People</div>
            <div class="people-grid" id="people-grid">
                {% for name in people_list %}
                <div class="person-card">
                    <div class="name">{{ name }}</div>
                    <div class="count">
                        <span class="num">{{ face_counts.get(name, 0) }}</span> faces
                    </div>
                    <button class="del" onclick="deletePerson('{{ name }}')">Delete</button>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <!-- Log Section -->
        <div class="section">
            <div class="section-title">Log</div>
            <div class="log-box" id="log-box">
                <div class="log-entry info">✓ System initialized</div>
            </div>
        </div>
    </div>

    <script>
        const csrfToken = {{ csrf_token|tojson }};
        // ==================== UI UPDATE ====================
        let systemReady = false;

        function updateStatus(data) {
            if (!systemReady && data.ready) {
                systemReady = true;
                addLog('✓ System ready', 'ok');
            }

            // Update counts
            document.getElementById('face-count').textContent = data.faces;
            document.getElementById('fps-val').textContent = data.fps;
            document.getElementById('people-count').textContent = data.people_count;
            document.getElementById('total-count').textContent = data.total_count;

            // Update status
            const dot = document.getElementById('status-dot');
            const text = document.getElementById('status-text');

            if (data.faces === 0) {
                dot.className = 'status-dot off';
                text.textContent = 'No face';
                text.style.color = '#888';
            } else if (data.match) {
                dot.className = 'status-dot on';
                text.textContent = data.name + ' ' + (data.confidence*100).toFixed(0) + '%';
                text.style.color = '#00ff88';
            } else if (data.confidence > 0) {
                dot.className = 'status-dot off';
                text.textContent = 'Low: ' + (data.confidence*100).toFixed(0) + '%';
                text.style.color = '#ffaa00';
            } else {
                dot.className = 'status-dot off';
                text.textContent = 'Face detected';
                text.style.color = '#ffaa00';
            }
        }

        // Fetch status every 500ms
        setInterval(() => {
            fetch('/status')
                .then(r => r.json())
                .then(data => updateStatus(data))
                .catch(e => console.error('Status error:', e));
        }, 500);

        // ==================== CONTROLS ====================
        function enrollFace() {
            const name = document.getElementById('enroll-name').value.trim();
            if (!name) return alert('Enter a name');

            fetch('/enroll_web', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ name })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    addLog('✓ Enrolled: ' + name + ' (' + data.count + ')', 'ok');
                    document.getElementById('enroll-name').value = '';
                    setTimeout(updatePeople, 100);
                } else {
                    addLog('✗ ' + data.message, 'err');
                }
            })
            .catch(e => addLog('✗ Error: ' + e, 'err'));
        }

        function deletePerson(name) {
            if (!confirm('Delete "' + name + '"?')) return;

            fetch('/delete_person', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ name })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    addLog('✓ Deleted: ' + name, 'ok');
                    setTimeout(updatePeople, 100);
                } else {
                    addLog('✗ Error', 'err');
                }
            });
        }

        function captureImage() {
            fetch('/capture', { method: 'POST', headers: { 'X-CSRF-Token': csrfToken } })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        addLog('✓ Captured: ' + data.filename, 'info');
                    }
                });
        }

        function updatePeople() {
            fetch('/get_people')
                .then(r => r.json())
                .then(data => {
                    const grid = document.getElementById('people-grid');
                    grid.innerHTML = '';
                    data.people.forEach(p => {
                        const card = document.createElement('div');
                        card.className = 'person-card';
                        card.innerHTML = `
                            <div class="name">👤 ${p.name}</div>
                            <div class="count"><span class="num">${p.count}</span> faces</div>
                            <button class="del" onclick="deletePerson('${p.name}')">Delete</button>
                        `;
                        grid.appendChild(card);
                    });
                });
        }

        function addLog(msg, type = 'info') {
            const log = document.getElementById('log-box');
            const entry = document.createElement('div');
            entry.className = 'log-entry ' + type;
            entry.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
        }

        function clearLog() {
            document.getElementById('log-box').innerHTML = '';
            addLog('Log cleared', 'info');
        }

        // Fetch status on load
        setTimeout(() => fetch('/status').then(r => r.json()).then(updateStatus), 500);
    </script>
</body>
</html>
'''

# ==================== STARTUP ====================
if __name__ == '__main__':
    hostname = socket.gethostname()

    try:
        ip_address = socket.gethostbyname(hostname)
    except OSError:
        ip_address = '127.0.0.1'

    print("\n" + "="*60)
    print("SMART LOCK WEB SERVER")
    print("="*60)
    print(f"\nStatus:")
    print(f"   People: {len(get_all_names())}")
    print(f"   Total faces: {get_person_count()}")
    print(f"   Threshold: {THRESHOLD*100}%")
    print(f"\nWeb Interface:")
    print(f"   http://localhost:{SERVER_PORT}")
    print(f"   http://{ip_address}:{SERVER_PORT}")
    print("\n" + "="*60 + "\n")

    # Run Flask
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=SERVER_DEBUG, threaded=SERVER_THREADED)
