"""MQTT bridge between the web/vision server and one ESP32 door lock."""

import json
import os
import re
import threading
import time
import uuid

try:
    import paho.mqtt.client as mqtt
except ImportError:  # Tests and camera-only development can run without MQTT.
    mqtt = None


DOOR_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,32}\Z")
DOOR_STATES = {"unknown", "closed", "opening", "open", "closing", "error"}


class DoorError(RuntimeError):
    """A door command could not be sent safely."""


class FaceTrigger:
    """Trigger once per appearance, then re-arm after the face is absent."""

    def __init__(self, rearm_seconds=2):
        self.rearm_seconds = rearm_seconds
        self.active_name = None
        self.missing_since = None

    def should_open(self, name, now=None):
        now = time.monotonic() if now is None else now
        if name:
            self.missing_since = None
            if name == self.active_name:
                return False
            self.active_name = name
            return True
        if self.active_name and self.missing_since is None:
            self.missing_since = now
        elif self.missing_since is not None and now - self.missing_since >= self.rearm_seconds:
            self.active_name = None
            self.missing_since = None
        return False


def _enabled(value):
    return value.strip().lower() in {"1", "true", "yes", "on"}


class DoorGateway:
    def __init__(self, client=None):
        self.enabled = _enabled(os.environ.get("MQTT_ENABLED", "false"))
        self.host = os.environ.get("MQTT_HOST", "127.0.0.1")
        self.port = int(os.environ.get("MQTT_PORT", "1883"))
        self.door_id = os.environ.get("MQTT_DOOR_ID", "front-door")
        self.open_seconds = int(os.environ.get("DOOR_OPEN_SECONDS", "5"))
        self.cooldown = float(os.environ.get("DOOR_COMMAND_COOLDOWN", "10"))
        if not DOOR_ID_RE.fullmatch(self.door_id):
            raise ValueError("MQTT_DOOR_ID must contain only letters, numbers, _ or -")
        if not 1 <= self.open_seconds <= 60:
            raise ValueError("DOOR_OPEN_SECONDS must be between 1 and 60")

        self.command_topic = f"smartlock/{self.door_id}/command"
        self.state_topic = f"smartlock/{self.door_id}/state"
        self.event_topic = f"smartlock/{self.door_id}/event"
        self._lock = threading.Lock()
        self._connected = False
        self._last_command = 0.0
        self._last_action = None
        self._state = {"status": "unknown", "online": False, "updated_at": None}
        self.client = client

        if self.enabled and self.client is None:
            if mqtt is None:
                raise RuntimeError("MQTT_ENABLED=true requires paho-mqtt")
            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=f"web-{self.door_id}",
                protocol=mqtt.MQTTv5,
            )
            password = os.environ.get("MQTT_WEB_PASSWORD", "")
            if len(password) < 12:
                raise ValueError("MQTT_WEB_PASSWORD must contain at least 12 characters")
            self.client.username_pw_set(
                "webapp",
                password,
            )
        if self.client is not None:
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

    def start(self):
        if not self.enabled:
            return
        self.client.connect_async(self.host, self.port, keepalive=30)
        self.client.loop_start()

    def stop(self):
        if self.enabled and self.client is not None:
            self.client.disconnect()
            self.client.loop_stop()

    def _on_connect(self, client, _userdata, _flags, reason_code, _properties):
        if hasattr(reason_code, "is_failure"):
            connected = not reason_code.is_failure
        else:
            connected = int(reason_code) == 0
        with self._lock:
            self._connected = connected
        if connected:
            client.subscribe([(self.state_topic, 1), (self.event_topic, 1)])

    def _on_disconnect(self, _client, _userdata, _flags, _reason_code, _properties):
        with self._lock:
            self._connected = False
            self._state["online"] = False

    def _on_message(self, _client, _userdata, message):
        if message.topic != self.state_topic:
            return
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            status = payload["status"]
            if status not in DOOR_STATES:
                return
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return
        with self._lock:
            self._state = {
                "status": status,
                "online": bool(payload.get("online", True)),
                "updated_at": payload.get("updated_at") or int(time.time()),
            }

    def snapshot(self):
        with self._lock:
            return {
                **self._state,
                "enabled": self.enabled,
                "connected": self._connected,
                "door_id": self.door_id,
            }

    def send(self, action, actor, source):
        """Publish an open/lock command; throttle only repeated actions."""
        if action not in {"open", "lock"}:
            raise ValueError("Action must be open or lock")
        with self._lock:
            if not self.enabled or not self._connected:
                raise DoorError("Bộ điều khiển cửa chưa kết nối")
            now = time.monotonic()
            if action == self._last_action and now - self._last_command < self.cooldown:
                return False
            self._last_command = now
            self._last_action = action

        command = {
            "action": action,
            "request_id": uuid.uuid4().hex,
            "actor": str(actor)[:64],
            "source": source,
            "sent_at": int(time.time()),
        }
        if action == "open":
            command["open_seconds"] = self.open_seconds
        payload = json.dumps(command, separators=(",", ":"))
        result = self.client.publish(self.command_topic, payload, qos=1, retain=False)
        if result.rc != 0:
            with self._lock:
                self._last_command = 0
            raise DoorError("Không gửi được lệnh mở cửa")
        return True
