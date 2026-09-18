"""Send laptop webcam frames to the Raspberry Pi TCP camera receiver."""

from __future__ import annotations

import argparse
import socket
import struct
import time
from typing import Optional

import cv2
import numpy as np


HEADER_FORMAT = "!II"
DEFAULT_PORT = 5001
DEFAULT_MAX_FRAME_BYTES = 524288


def encode_frame(
    frame: np.ndarray,
    sequence: int,
    quality: int,
    max_frame_bytes: int,
) -> bytes:
    """Encode a BGR frame using the TCP receiver's wire format."""
    encoded, buffer = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, quality],
    )
    if not encoded:
        raise ValueError("Could not encode camera frame as JPEG")

    payload = buffer.tobytes()
    if len(payload) > max_frame_bytes:
        raise ValueError(
            f"JPEG frame is {len(payload)} bytes; maximum is {max_frame_bytes} bytes"
        )

    header = struct.pack(HEADER_FORMAT, len(payload), sequence & 0xFFFFFFFF)
    return header + payload


def open_camera(camera_id: int, width: int, height: int, fps: int) -> cv2.VideoCapture:
    """Open and configure the laptop camera."""
    camera = cv2.VideoCapture(camera_id)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    camera.set(cv2.CAP_PROP_FPS, fps)

    if not camera.isOpened():
        camera.release()
        raise RuntimeError(f"Cannot open laptop camera {camera_id}")
    return camera


def connect(host: str, port: int, retry_seconds: float) -> socket.socket:
    """Connect to the Raspberry Pi, retrying until it becomes reachable."""
    while True:
        try:
            print(f"Connecting to {host}:{port}...")
            connection = socket.create_connection((host, port), timeout=10)
            print("Connected. Sending camera frames; press Ctrl+C to stop.")
            return connection
        except OSError as exc:
            print(f"Connection failed: {exc}; retrying in {retry_seconds:g}s")
            time.sleep(retry_seconds)


def send_camera(args: argparse.Namespace) -> None:
    camera: Optional[cv2.VideoCapture] = None
    connection: Optional[socket.socket] = None
    sequence = 0
    frame_interval = 1.0 / args.fps

    try:
        camera = open_camera(args.camera, args.width, args.height, args.fps)
        while True:
            started_at = time.monotonic()
            ok, frame = camera.read()
            if not ok or frame is None:
                raise RuntimeError("Laptop camera returned no frame")

            packet = encode_frame(
                frame,
                sequence=sequence,
                quality=args.quality,
                max_frame_bytes=args.max_frame_bytes,
            )

            if connection is None:
                connection = connect(args.host, args.port, args.retry_seconds)

            try:
                connection.sendall(packet)
            except OSError as exc:
                print(f"Connection lost: {exc}")
                connection.close()
                connection = None
                continue

            sequence = (sequence + 1) & 0xFFFFFFFF
            remaining = frame_interval - (time.monotonic() - started_at)
            if remaining > 0:
                time.sleep(remaining)
    finally:
        if connection is not None:
            connection.close()
        if camera is not None:
            camera.release()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a laptop webcam to the Smart Lock Raspberry Pi server."
    )
    parser.add_argument("--host", required=True, help="Raspberry Pi IP or hostname")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--camera", type=int, default=0, help="Laptop camera index")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--quality", type=int, choices=range(1, 101), default=80)
    parser.add_argument("--max-frame-bytes", type=int, default=DEFAULT_MAX_FRAME_BYTES)
    parser.add_argument("--retry-seconds", type=float, default=3.0)
    return parser.parse_args()


if __name__ == "__main__":
    try:
        send_camera(parse_args())
    except KeyboardInterrupt:
        print("\nCamera sender stopped.")
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(f"Camera sender error: {exc}") from exc