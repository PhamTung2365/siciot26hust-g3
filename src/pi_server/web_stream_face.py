import os
import socket
import threading
import time

import cv2
from flask import Flask, Response, jsonify, redirect, render_template, request, url_for

from pi_server.auth import (
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
from pi_server.config import (
    CAMERA_DEVICE_ID,
    CAMERA_FPS,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CAPTURES_DIR,
    SERVER_DEBUG,
    SERVER_HOST,
    SERVER_PORT,
    SERVER_THREADED,
    TCP_CAMERA_ENABLED,
    TCP_CAMERA_HOST,
    TCP_CAMERA_PORT,
    TCP_CAMERA_TIMEOUT,
    TCP_FRAME_MAX_BYTES,
    VIDEO_FPS_DISPLAY_INTERVAL,
    VIDEO_QUALITY,
    VIDEO_SHOW_LANDMARKS,
)
from pi_server.tcp_camera import TcpCameraReceiver


# Import modules
from pi_server.face_db import (
    THRESHOLD,
    add_face,
    delete_person,
    get_all_names,
    get_all_people_with_counts,
    get_person_count,
    recognize_face,
)
from pi_server.face_utils import get_face_embedding, get_model_info
from pi_server.mqtt_gateway import DoorError, DoorGateway, FaceTrigger

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
door = DoorGateway()
face_trigger = FaceTrigger()

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

# Initialize TCP Camera Receiver
tcp_camera = None
if TCP_CAMERA_ENABLED:
    tcp_camera = TcpCameraReceiver(
        host=TCP_CAMERA_HOST,
        port=TCP_CAMERA_PORT,
        max_frame_bytes=TCP_FRAME_MAX_BYTES,
        timeout=TCP_CAMERA_TIMEOUT,
    )
    tcp_camera.start()

cap, device_id = init_camera()
if cap is None and (tcp_camera is None or not tcp_camera.get_stats()['enabled']):
    print("Server will start without video; connect a camera and restart")


def read_frame():
    """Read one frame prioritizing ESP32-CAM TCP stream, falling back to local camera."""
    if tcp_camera is not None:
        ret, frame = tcp_camera.get_frame(max_age=5.0)
        if ret and frame is not None:
            return True, frame

    if cap is not None:
        with camera_lock:
            return cap.read()

    return False, None



def timestamp():
    """Filename-safe timestamp with sub-second collision protection."""
    return f"{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1_000_000_000:09d}"

# ==================== VIDEO STREAM ====================
frame_condition = threading.Condition()
latest_frame = None
frame_sequence = 0
services_started = False


def process_frames():
    """Continuously recognize faces and publish the latest annotated frame."""
    global latest_frame, frame_sequence
    frame_count = 0
    fps = 0.0
    fps_start = time.time()

    while True:
        ret, frame = read_frame()
        if not ret:
            with state.lock:
                state.is_ready = False
            time.sleep(0.5)
            continue

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
                state.match = bool(name is not None and confidence >= THRESHOLD)
                state.name = name if name else 'Unknown'
                state.confidence = float(confidence) if confidence else 0.0

            # Draw result
            if name and confidence >= THRESHOLD:
                text = f"{name} ({confidence*100:.1f}%)"
                color = (0, 255, 0)  # Green
                if door.snapshot()["connected"] and face_trigger.should_open(name):
                    try:
                        door.send("open", name, "face")
                    except DoorError:
                        pass
            else:
                face_trigger.should_open(None)
                text = f"Unknown ({confidence*100:.1f}%)"
                color = (0, 0, 255)  # Red

            cv2.putText(frame, text,
                       (bbox[0], bbox[3]+25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        else:
            face_trigger.should_open(None)
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

        with frame_condition:
            latest_frame = buffer.tobytes()
            frame_sequence += 1
            frame_condition.notify_all()


def generate_frames():
    """Yield frames produced by the background recognition worker."""
    seen = -1
    while True:
        with frame_condition:
            frame_condition.wait_for(lambda: frame_sequence != seen, timeout=5)
            if latest_frame is None:
                continue
            seen, frame_bytes = frame_sequence, latest_frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame_bytes + b'\r\n')


def start_services():
    """Start long-running MQTT and vision workers exactly once."""
    global services_started
    if services_started:
        return
    services_started = True
    door.start()
    threading.Thread(target=process_frames, name="vision", daemon=True).start()

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    user = current_user()
    if user is None:
        return redirect(url_for('login'))
    return render_template(
        'dashboard.html',
        is_admin=user['role'] == 'admin',
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
    tcp_stats = tcp_camera.get_stats() if tcp_camera else None
    camera_source = 'tcp' if (tcp_stats and tcp_stats.get('is_fresh')) else ('local' if cap is not None else 'none')

    with state.lock:
        return jsonify({
            'ready': state.is_ready,
            'faces': state.faces,
            'fps': state.fps,
            'match': bool(state.match),
            'name': state.name,
            'confidence': float(round(state.confidence, 3)),
            'people_count': len(get_all_names()),
            'total_count': get_person_count(),
            'camera_source': camera_source,
            'tcp_camera': tcp_stats,
            'door': door.snapshot(),
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
    tcp_stats = tcp_camera.get_stats() if tcp_camera else None
    camera_source = 'tcp' if (tcp_stats and tcp_stats.get('is_fresh')) else ('local' if cap is not None else 'none')

    return jsonify({
        'model': get_model_info(),
        'camera': device_id,
        'camera_source': camera_source,
        'tcp_camera': tcp_stats,
        'threshold': THRESHOLD,
        'people': len(get_all_names()),
        'total_faces': get_person_count()
    })


@app.route('/api/door/command', methods=['POST'])
@login_required
@csrf_protect
def control_door():
    """Allow an authenticated operator to open or lock the door."""
    user = current_user()
    action = (request.get_json(silent=True) or {}).get('action')
    if action not in {'open', 'lock'}:
        return jsonify({'status': 'error', 'message': 'Lệnh cửa không hợp lệ'}), 400
    try:
        sent = door.send(action, user['username'], 'web')
    except DoorError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 503
    if not sent:
        return jsonify({'status': 'error', 'message': 'Vui lòng chờ trước khi gửi lại lệnh'}), 429
    message = 'Đã gửi lệnh mở khóa' if action == 'open' else 'Đã gửi lệnh khóa cửa'
    return jsonify({'status': 'success', 'message': message})



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
    if TCP_CAMERA_ENABLED:
        print(f"   TCP Socket Camera: {TCP_CAMERA_HOST}:{TCP_CAMERA_PORT} (Active)")
    print(f"\nWeb Interface:")
    print(f"   http://localhost:{SERVER_PORT}")
    print(f"   http://{ip_address}:{SERVER_PORT}")
    print("\n" + "="*60 + "\n")

    start_services()
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=SERVER_DEBUG, threaded=SERVER_THREADED)
