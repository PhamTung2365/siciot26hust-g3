"""End-to-end auth and authorization checks without a camera."""

import os
import tempfile
import unittest
from unittest.mock import patch

# These must exist before importing web_stream_face, which bootstraps auth.
_database = tempfile.TemporaryDirectory()
os.environ.update(
    FLASK_SECRET_KEY="test-secret",
    ADMIN_USERNAME="admin",
    ADMIN_PASSWORD="strong-admin-password",
    AUTH_DB_PATH=f"{_database.name}/import-users.db",
)

import pi_server.auth as auth
import pi_server.web_stream_face as web


class WebAuthTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        web.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        auth.init_auth(web.app, f"{self.directory.name}/users.db")
        self.client = web.app.test_client()

    def tearDown(self):
        self.directory.cleanup()

    def csrf(self):
        self.client.get("/login")
        with self.client.session_transaction() as session:
            return session["csrf_token"]

    def login(self, username, password):
        response = self.client.post(
            "/login",
            data={"username": username, "password": password, "csrf_token": self.csrf()},
        )
        self.assertEqual(response.status_code, 302)

    def test_anonymous_requests_are_blocked(self):
        for path in ("/", "/status", "/info", "/api/admin/users"):
            self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.post("/api/door/command").status_code, 401)

    def test_stitch_ui_pages_render_for_their_roles(self):
        self.assertIn(b"SMART LOCK", self.client.get("/login").data)
        self.login("admin", "strong-admin-password")
        self.assertIn("Cửa chính".encode(), self.client.get("/").data)
        self.assertIn("Quản lý tài khoản".encode(), self.client.get("/admin/users").data)

    def test_admin_creates_user_and_csrf_is_required(self):
        self.login("admin", "strong-admin-password")
        self.assertEqual(
            self.client.post("/api/admin/users", json={"username": "alice", "password": "strong-password"}).status_code,
            400,
        )
        response = self.client.post(
            "/api/admin/users",
            json={"username": "alice", "password": "strong-password"},
            headers={"X-CSRF-Token": self.csrf()},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["user"]["role"], "user")
        with web.app.app_context():
            self.assertEqual(auth.authenticate("alice", "strong-password")["role"], "user")

    def test_user_has_basic_access_only_and_can_change_password(self):
        with web.app.app_context():
            auth.create_user("alice", "strong-password")
        self.login("alice", "strong-password")
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/status").status_code, 200)
        self.assertEqual(self.client.get("/info").status_code, 200)
        self.assertIn("door", self.client.get("/status").json)
        self.assertEqual(self.client.get("/admin/users").status_code, 403)
        self.assertEqual(self.client.get("/api/admin/users").status_code, 403)
        for path, payload in (
            ("/api/admin/users", {"username": "bob", "password": "strong-password"}),
            ("/enroll_web", {"name": "Alice"}),
            ("/delete_person", {"name": "Alice"}),
            ("/capture", {}),
        ):
            self.assertEqual(self.client.post(path, json=payload).status_code, 403)
        self.assertEqual(self.client.get("/get_people").status_code, 403)
        self.assertEqual(self.client.post("/api/door/command", json={"action": "open"}).status_code, 400)
        with patch.object(web.door, "send", return_value=True) as send_command:
            self.assertEqual(
                self.client.post(
                    "/api/door/command",
                    json={"action": "lock"},
                    headers={"X-CSRF-Token": self.csrf()},
                ).status_code,
                200,
            )
            send_command.assert_called_once_with("lock", "alice", "web")
        response = self.client.post(
            "/change-password",
            data={
                "current_password": "strong-password",
                "new_password": "new-strong-password",
                "confirm_password": "new-strong-password",
                "csrf_token": self.csrf(),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Password changed.", response.data)
        with web.app.app_context():
            self.assertIsNone(auth.authenticate("alice", "strong-password"))
            self.assertEqual(auth.authenticate("alice", "new-strong-password")["username"], "alice")

    def test_logout_requires_csrf_and_clears_session(self):
        self.login("admin", "strong-admin-password")
        self.assertEqual(self.client.post("/logout").status_code, 400)
        self.assertEqual(self.client.post("/logout", data={"csrf_token": self.csrf()}).status_code, 302)
        self.assertEqual(self.client.get("/status").status_code, 401)


if __name__ == "__main__":
    unittest.main()
