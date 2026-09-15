#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$PROJECT_DIR/venv/bin/python"

require_env() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo "Thiếu .env. Hãy copy .env.example thành .env và thay toàn bộ secret."
        exit 1
    fi
}

case "${1:-help}" in
    setup)
        mkdir -p "$PROJECT_DIR/faces_db" "$PROJECT_DIR/captures" "$PROJECT_DIR/data"
        [ -d "$PROJECT_DIR/venv" ] || python3 -m venv "$PROJECT_DIR/venv"
        "$PYTHON" -m pip install --upgrade pip setuptools wheel
        "$PYTHON" -m pip install -r "$PROJECT_DIR/requirements.txt"
        ;;
    mqtt-init)
        require_env
        mkdir -p "$PROJECT_DIR/data/mqtt"
        cd "$PROJECT_DIR"
        docker compose run --rm --no-deps --entrypoint sh mqtt -c '
          touch /mosquitto/data/password.txt
          mosquitto_passwd -b /mosquitto/data/password.txt webapp "$MQTT_WEB_PASSWORD"
          mosquitto_passwd -b /mosquitto/data/password.txt esp32 "$MQTT_DEVICE_PASSWORD"
          chown 1883:1883 /mosquitto/data/password.txt
          chmod 600 /mosquitto/data/password.txt
        '
        ;;
    start)
        require_env
        if [ ! -x "$PYTHON" ]; then
            echo "Chưa có virtualenv. Chạy: bash smartlock.sh setup"
            exit 1
        fi
        cd "$PROJECT_DIR/.."
        exec "$PYTHON" -m pi_server.web_stream_face
        ;;
    test)
        if [ ! -x "$PYTHON" ]; then
            echo "Chưa có virtualenv. Chạy: bash smartlock.sh setup"
            exit 1
        fi
        cd "$PROJECT_DIR/.."
        "$PYTHON" -m unittest discover -v pi_server/tests
        "$PYTHON" -m compileall -q pi_server
        ;;
    docker)
        require_env
        cd "$PROJECT_DIR"
        docker compose up --build -d
        ;;
    *)
        echo "Dùng: bash smartlock.sh {setup|mqtt-init|start|test|docker}"
        ;;
esac
