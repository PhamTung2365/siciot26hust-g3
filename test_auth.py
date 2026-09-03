import os
import tempfile
import unittest

from flask import Flask, session

import auth


class AuthTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.old_env = {key: os.environ.get(key) for key in ("ADMIN_USERNAME", "ADMIN_PASSWORD")}
        os.environ.update(ADMIN_USERNAME="admin", ADMIN_PASSWORD="strong-admin-password")
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "test-secret"
        auth.init_auth(self.app, f"{self.directory.name}/users.db")

    def tearDown(self):
        for key, value in self.old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.directory.cleanup()

    def test_bootstrap_create_and_change_password(self):
        with self.app.app_context():
            self.assertEqual(auth.authenticate("admin", "strong-admin-password")["role"], "admin")
            self.assertEqual(auth.create_user("normal.user", "strong-user-password")["role"], "user")
            with self.assertRaises(auth.AuthError):
                auth.create_user("normal.user", "strong-user-password")
            auth.change_password("normal.user", "strong-user-password", "new-strong-password")
            self.assertIsNone(auth.authenticate("normal.user", "strong-user-password"))
            self.assertEqual(auth.authenticate("normal.user", "new-strong-password")["username"], "normal.user")

    def test_session_and_csrf(self):
        with self.app.test_request_context():
            auth.sign_in({"username": "admin", "role": "admin"})
            self.assertEqual(auth.current_user()["username"], "admin")
            self.assertTrue(auth.validate_csrf(session["csrf_token"]))
            self.assertFalse(auth.validate_csrf("wrong"))


if __name__ == "__main__":
    unittest.main()
