"""
Unit tests for TCP socket camera receiver.
"""

import socket
import struct
import time
import unittest
import numpy as np
import cv2

from pi_server.tcp_camera import (
    ProtocolError,
    TcpCameraReceiver,
    read_frame_from_socket,
    recv_exact,
)


class DummySocket:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def recv(self, size: int) -> bytes:
        if self.offset >= len(self.data):
            return b""
        chunk = self.data[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


def create_dummy_jpeg() -> bytes:
    """Create a minimal valid BGR image encoded as JPEG."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.putText(img, "TEST", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    ret, buf = cv2.imencode(".jpg", img)
    assert ret
    return buf.tobytes()


class TcpCameraTest(unittest.TestCase):
    def test_recv_exact_complete(self):
        sock = DummySocket(b"12345678")
        self.assertEqual(recv_exact(sock, 8), b"12345678")

    def test_recv_exact_eof(self):
        sock = DummySocket(b"")
        self.assertIsNone(recv_exact(sock, 8))

    def test_recv_exact_partial_fails(self):
        sock = DummySocket(b"1234")
        with self.assertRaises(ConnectionError):
            recv_exact(sock, 8)

    def test_read_frame_valid(self):
        jpeg_bytes = create_dummy_jpeg()
        header = struct.pack("!II", len(jpeg_bytes), 42)
        sock = DummySocket(header + jpeg_bytes)

        res = read_frame_from_socket(sock, max_frame_bytes=524288)
        self.assertIsNotNone(res)
        seq, payload = res
        self.assertEqual(seq, 42)
        self.assertEqual(payload, jpeg_bytes)

    def test_read_frame_invalid_length(self):
        header = struct.pack("!II", 1000000, 1)
        sock = DummySocket(header)
        with self.assertRaises(ProtocolError):
            read_frame_from_socket(sock, max_frame_bytes=524288)

    def test_read_frame_invalid_jpeg_markers(self):
        payload = b"NOT_A_JPEG_FILE"
        header = struct.pack("!II", len(payload), 1)
        sock = DummySocket(header + payload)
        with self.assertRaises(ProtocolError):
            read_frame_from_socket(sock, max_frame_bytes=524288)

    def test_tcp_camera_receiver_e2e(self):
        # Find unused port
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_sock.bind(('127.0.0.1', 0))
        port = temp_sock.getsockname()[1]
        temp_sock.close()

        receiver = TcpCameraReceiver(host='127.0.0.1', port=port, timeout=2.0)
        receiver.start()
        time.sleep(0.2)

        try:
            # Connect simulated client
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', port))

            jpeg = create_dummy_jpeg()

            # Send frame 0
            header0 = struct.pack("!II", len(jpeg), 0)
            client.sendall(header0 + jpeg)

            # Send frame 1
            header1 = struct.pack("!II", len(jpeg), 1)
            client.sendall(header1 + jpeg)

            time.sleep(0.3)

            stats = receiver.get_stats()
            self.assertTrue(stats['connected'])
            self.assertEqual(stats['frames_received'], 2)
            self.assertEqual(stats['latest_sequence'], 1)
            self.assertTrue(stats['is_fresh'])

            ret, frame = receiver.get_frame(max_age=2.0)
            self.assertTrue(ret)
            self.assertIsNotNone(frame)
            self.assertEqual(frame.shape[0], 100)
            self.assertEqual(frame.shape[1], 100)

            client.close()
            time.sleep(0.2)

            stats_after = receiver.get_stats()
            self.assertFalse(stats_after['connected'])

        finally:
            receiver.stop()


if __name__ == '__main__':
    unittest.main()
