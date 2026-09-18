#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$PROJECT_DIR/venv/bin/python"

require_env() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo "Thiếu .env. Hãy copy env.example thành .env và thay toàn bộ secret."
        exit 1
    fi
}

case "${1:-help}" in
    setup)
        mkdir -p "$PROJECT_DIR/faces_db" "$PROJECT_DIR/captures" "$PROJECT_DIR/data"
        if [ ! -x "$PYTHON" ]; then
            python3 -m venv --clear "$PROJECT_DIR/venv"
        fi
        "$PYTHON" -m pip install --upgrade pip setuptools wheel
        "$PYTHON" -m pip install -r "$PROJECT_DIR/requirements.txt"
        ;;
    mqtt-init)
        require_env
        if ! command -v docker >/dev/null 2>&1; then
            echo "Chưa cài Docker. Hãy cài Docker Engine và Docker Compose plugin rồi chạy lại: bash smartlock.sh mqtt-init" >&2
            exit 1
        fi
        if ! docker compose version >/dev/null 2>&1; then
            echo "Docker Compose plugin chưa sẵn sàng. Hãy cài Docker Compose plugin rồi chạy lại: bash smartlock.sh mqtt-init" >&2
            exit 1
        fi
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
        if command -v ss >/dev/null 2>&1; then
            if ss -ltn | awk '$4 ~ /:5000$/ || $4 ~ /:5001$/ {found=1} END {exit !found}'; then
                echo "Server đã chạy hoặc cổng 5000/5001 đang được sử dụng." >&2
                echo "Kiểm tra: ss -ltnp | grep -E ':5000|:5001'" >&2
                exit 1
            fi
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
