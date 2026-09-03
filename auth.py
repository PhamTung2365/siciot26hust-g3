"""Small SQLite-backed authentication helpers for the Smart Lock web app."""

import os
import re
import secrets
import sqlite3
import time
from functools import wraps
from pathlib import Path

from flask import abort, current_app, session
from werkzeug.security import check_password_hash, generate_password_hash


USERNAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,31}\Z")
MIN_PASSWORD_LENGTH = 8


class AuthError(ValueError):
    """An authentication or validation error safe to show to a user."""


def _load_env(path):
    """Load the simple KEY=value values needed for local development."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _db_path():
    return current_app.config["AUTH_DB_PATH"]


def _connect():
    connection = sqlite3.connect(_db_path())
    connection.row_factory = sqlite3.Row
    return connection


def _validate_username(username):
    if not isinstance(username, str) or not USERNAME_RE.fullmatch(username):
        raise AuthError("Username must be 3-32 letters, numbers, ., _ or -")
    return username


def _validate_password(password):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > 1024:
        raise AuthError("Password is too long")
    return password


def _public_user(row):
    return {"username": row["username"], "role": row["role"], "created_at": row["created_at"]}


def init_auth(app, db_path=None):
    """Configure Flask sessions, create the user table, and create the first admin."""
    _load_env(Path(app.root_path) / ".env")
    secret_key = app.config.get("SECRET_KEY") or os.environ.get("FLASK_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("FLASK_SECRET_KEY must be set in .env or the environment")
    app.config["SECRET_KEY"] = secret_key
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config["AUTH_DB_PATH"] = str(
        db_path or app.config.get("AUTH_DB_PATH") or os.environ.get("AUTH_DB_PATH")
        or Path(app.root_path) / "users.db"
    )

    with app.app_context():
        with _connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
                    created_at INTEGER NOT NULL
                )"""
            )
        bootstrap_admin()


def bootstrap_admin():
    """Create the configured admin once; existing accounts are never overwritten."""
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")
    if not username or not password:
        raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env or the environment")
    _validate_username(username)
    _validate_password(password)
    with _connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role, created_at) VALUES (?, ?, 'admin', ?)",
            (username, generate_password_hash(password), int(time.time())),
        )


def authenticate(username, password):
    """Return a safe user record for valid credentials, otherwise None."""
    if not isinstance(username, str) or not isinstance(password, str):
        return None
    with _connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return _public_user(row) if row and check_password_hash(row["password_hash"], password) else None


def create_user(username, password):
    """Create an ordinary user. There is intentionally no public sign-up path."""
    username, password = _validate_username(username), _validate_password(password)
    created_at = int(time.time())
    try:
        with _connect() as connection:
            connection.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, 'user', ?)",
                (username, generate_password_hash(password), created_at),
            )
    except sqlite3.IntegrityError as error:
        raise AuthError("Username already exists") from error
    return {"username": username, "role": "user", "created_at": created_at}


def list_users():
    with _connect() as connection:
        rows = connection.execute("SELECT username, role, created_at FROM users ORDER BY username").fetchall()
    return [_public_user(row) for row in rows]


def change_password(username, current_password, new_password):
    """Change one account password after checking its current password."""
    username = _validate_username(username)
    new_password = _validate_password(new_password)
    user = authenticate(username, current_password)
    if not user:
        raise AuthError("Current password is incorrect")
    with _connect() as connection:
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (generate_password_hash(new_password), username),
        )


def sign_in(user):
    session.clear()
    session["user"] = {"username": user["username"], "role": user["role"]}
    csrf_token()


def sign_out():
    session.clear()


def current_user():
    user = session.get("user")
    if not isinstance(user, dict) or user.get("role") not in {"admin", "user"}:
        return None
    username = user.get("username")
    if not isinstance(username, str):
        return None
    with _connect() as connection:
        row = connection.execute("SELECT username, role, created_at FROM users WHERE username = ?", (username,)).fetchone()
    return _public_user(row) if row else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            abort(401)
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            abort(401)
        if user["role"] != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def csrf_token():
    return session.setdefault("csrf_token", secrets.token_urlsafe(32))


def validate_csrf(token=None):
    expected = session.get("csrf_token")
    return bool(expected and token and secrets.compare_digest(expected, token))


def csrf_protect(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        from flask import request
        token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        if not validate_csrf(token):
            abort(400, "Invalid CSRF token")
        return view(*args, **kwargs)
    return wrapped
