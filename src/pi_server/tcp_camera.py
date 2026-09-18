"""
TCP Socket Camera Receiver for ESP32-CAM frame streaming.
Receives big-endian 8-byte framed JPEG images:
- Bytes 0..3: JPEG byte length (uint32, big-endian)
- Bytes 4..7: Sequence number (uint32, big-endian)
- Bytes 8.. : JPEG payload bytes
"""

from __future__ import annotations

import os
import socket
import struct
import threading
import time
from typing import Any, Optional, Tuple

import cv2
import numpy as np

HEADER_SIZE = 8


class ProtocolError(ValueError):
    """Raised when incoming socket payload violates protocol constraints."""
    pass


def recv_exact(sock: socket.socket, size: int) -> Optional[bytes]:
    """Read exactly `size` bytes from socket. Return None on clean EOF before any data."""
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            if not data:
                return None
            raise ConnectionError("Connection closed mid-frame")
        data.extend(chunk)
    return bytes(data)


def read_frame_from_socket(sock: socket.socket, max_frame_bytes: int) -> Optional[Tuple[int, bytes]]:
    """Read and validate a single framed JPEG frame from a TCP socket."""
    header = recv_exact(sock, HEADER_SIZE)
    if header is None:
        return None

    length, sequence = struct.unpack("!II", header)
    if not (1 <= length <= max_frame_bytes):
        raise ProtocolError(f"Invalid JPEG length: {length} (max allowed: {max_frame_bytes})")

    payload = recv_exact(sock, length)
    if payload is None:
        raise ConnectionError("Connection closed before JPEG payload finished")

    if len(payload) < 4 or payload[:2] != b"\xff\xd8" or payload[-2:] != b"\xff\xd9":
        raise ProtocolError("Invalid JPEG SOI/EOI markers")

    return sequence, payload


class TcpCameraReceiver:
    """Background TCP socket server that receives JPEG frame streams from ESP32-CAM."""

    def __init__(self, host: str = '0.0.0.0', port: int = 5001, max_frame_bytes: int = 524288, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.max_frame_bytes = max_frame_bytes
        self.timeout = timeout

        self._lock = threading.Lock()
        self._server_sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

        # State
        self.latest_frame: Optional[np.ndarray] = None
        self.latest_timestamp: float = 0.0
        self.latest_sequence: int = 0
        self.client_ip: Optional[str] = None
        self.frames_received: int = 0
        self.sequence_gaps: int = 0
        self.is_connected: bool = False

        # FPS calculation
        self._fps: float = 0.0
        self._fps_count: int = 0
        self._fps_start: float = time.time()

    def start(self) -> None:
        """Start the background TCP server thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._server_loop, daemon=True, name="TcpCameraThread")
        self._thread.start()

    def stop(self) -> None:
        """Stop the TCP server thread and close sockets."""
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _server_loop(self) -> None:
        """Main TCP socket server loop."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen(1)
            sock.settimeout(2.0)  # Periodic check of self._running
            self._server_sock = sock
            print(f"[TCP Camera] Server listening on {self.host}:{self.port}")
        except Exception as exc:
            print(f"[TCP Camera] Failed to bind server on {self.host}:{self.port} - {exc}")
            self._running = False
            return

        while self._running:
            try:
                conn, addr = sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            client_addr_str = f"{addr[0]}:{addr[1]}"
            print(f"[TCP Camera] ESP32-CAM connected from {client_addr_str}")

            with self._lock:
                self.client_ip = addr[0]
                self.is_connected = True

            try:
                self._handle_client(conn)
            except (ConnectionError, ProtocolError, OSError) as exc:
                print(f"[TCP Camera] Client {client_addr_str} disconnected: {exc}")
            finally:
                conn.close()
                with self._lock:
                    self.is_connected = False
                    self.client_ip = None

    def _handle_client(self, conn: socket.socket) -> None:
        """Process incoming frames from a single connected ESP32 client."""
        conn.settimeout(self.timeout)
        expected_seq: Optional[int] = None

        while self._running:
            result = read_frame_from_socket(conn, self.max_frame_bytes)
            if result is None:
                break

            seq, payload = result

            # Check for sequence gap
            if expected_seq is not None and seq != expected_seq:
                with self._lock:
                    self.sequence_gaps += 1
            expected_seq = (seq + 1) & 0xFFFFFFFF

            # Decode JPEG to BGR
            frame = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                print("[TCP Camera] Failed to decode JPEG frame")
                continue

            now = time.time()
            with self._lock:
                self.latest_frame = frame
                self.latest_timestamp = now
                self.latest_sequence = seq
                self.frames_received += 1

                # Update FPS
                self._fps_count += 1
                elapsed = now - self._fps_start
                if elapsed >= 2.0:
                    self._fps = self._fps_count / elapsed
                    self._fps_count = 0
                    self._fps_start = now

    def get_frame(self, max_age: float = 5.0) -> Tuple[bool, Optional[np.ndarray]]:
        """Get latest valid BGR frame if received within `max_age` seconds."""
        with self._lock:
            if self.latest_frame is None:
                return False, None
            if time.time() - self.latest_timestamp > max_age:
                return False, None
            return True, self.latest_frame.copy()

    def get_stats(self) -> dict[str, Any]:
        """Return current status and metrics dictionary."""
        with self._lock:
            now = time.time()
            is_fresh = (self.latest_frame is not None) and ((now - self.latest_timestamp) <= 5.0)
            return {
                'enabled': True,
                'port': self.port,
                'connected': self.is_connected,
                'client_ip': self.client_ip,
                'frames_received': self.frames_received,
                'latest_sequence': self.latest_sequence,
                'sequence_gaps': self.sequence_gaps,
                'fps': round(self._fps, 1),
                'is_fresh': is_fresh,
                'last_frame_age': round(now - self.latest_timestamp, 2) if self.latest_timestamp else None,
            }
