from __future__ import annotations

import re
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings


password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
EMAIL_PATTERN = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
AUTH_COOKIE = 'databricks_access_token'


def _connection() -> sqlite3.Connection:
    database_path = Path(settings.database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    connection.execute(
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )'''
    )
    connection.execute(
        '''CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )'''
    )
    connection.execute(
        '''CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id)
        )'''
    )
    return connection


def initialize_database() -> None:
    with _connection() as connection:
        connection.execute('SELECT 1')


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email(email: str) -> str:
    normalized = normalize_email(email)
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=422, detail='Enter a valid email address.')
    return normalized


def validate_password(password: str) -> str:
    if len(password.encode('utf-8')) > 72:
        raise HTTPException(status_code=422, detail='Password cannot exceed 72 bytes for bcrypt compatibility.')
    if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
        raise HTTPException(status_code=422, detail='Password must be at least 8 characters and include uppercase, lowercase, and a number.')
    return password


def create_user(full_name: str, email: str, password: str) -> dict[str, Any]:
    full_name = full_name.strip()
    if not full_name:
        raise HTTPException(status_code=422, detail='Full name is required.')
    email = validate_email(email)
    validate_password(password)
    now = datetime.now(timezone.utc).isoformat()
    try:
        with _connection() as connection:
            cursor = connection.execute(
                'INSERT INTO users (full_name, email, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                (full_name, email, password_context.hash(password), now, now),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail='An account with this email already exists.')
    return get_user(int(user_id))


def get_user(user_id: int) -> dict[str, Any]:
    with _connection() as connection:
        row = connection.execute('SELECT id, full_name, email, created_at, updated_at FROM users WHERE id = ?', (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='User account not found.')
    return dict(row)


def get_conversation(user_id: int, conversation_id: str) -> dict[str, Any]:
    with _connection() as connection:
        row = connection.execute(
            'SELECT id, user_id, title, created_at, updated_at FROM conversations WHERE user_id = ? AND id = ?',
            (user_id, conversation_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='Conversation not found.')
    return dict(row)


def create_conversation(user_id: int, title: str | None = None, conversation_id: str | None = None) -> dict[str, Any]:
    user = get_user(user_id)
    conversation_id = conversation_id or f'conv-{uuid.uuid4().hex}'
    created_at = datetime.now(timezone.utc).isoformat()
    if title is None or not title.strip():
        title = 'New Chat'
    title = title.strip()
    with _connection() as connection:
        connection.execute(
            'INSERT INTO conversations (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
            (conversation_id, user['id'], title, created_at, created_at),
        )
    return get_conversation(user['id'], conversation_id)


def update_conversation_title(user_id: int, conversation_id: str, title: str) -> dict[str, Any]:
    conversation = get_conversation(user_id, conversation_id)
    normalized_title = ' '.join(title.strip().split()) or 'New Chat'
    updated_at = datetime.now(timezone.utc).isoformat()
    with _connection() as connection:
        connection.execute(
            'UPDATE conversations SET title = ?, updated_at = ? WHERE user_id = ? AND id = ?',
            (normalized_title, updated_at, user_id, conversation_id),
        )
    conversation['title'] = normalized_title
    conversation['updated_at'] = updated_at
    return conversation


def list_conversations(user_id: int) -> list[dict[str, Any]]:
    get_user(user_id)
    with _connection() as connection:
        rows = connection.execute(
            'SELECT id, user_id, title, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_message(user_id: int, conversation_id: str, role: str, content: str) -> dict[str, Any]:
    get_conversation(user_id, conversation_id)
    created_at = datetime.now(timezone.utc).isoformat()
    with _connection() as connection:
        cursor = connection.execute(
            'INSERT INTO conversation_messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)',
            (conversation_id, role, content, created_at),
        )
    return {
        'id': cursor.lastrowid,
        'conversation_id': conversation_id,
        'role': role,
        'content': content,
        'created_at': created_at,
    }


def get_conversation_messages(user_id: int, conversation_id: str) -> list[dict[str, Any]]:
    get_conversation(user_id, conversation_id)
    with _connection() as connection:
        rows = connection.execute(
            'SELECT id, conversation_id, role, content, created_at FROM conversation_messages WHERE conversation_id = ? ORDER BY created_at ASC, id ASC',
            (conversation_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_conversation(user_id: int, conversation_id: str) -> None:
    get_conversation(user_id, conversation_id)
    with _connection() as connection:
        connection.execute('DELETE FROM conversation_messages WHERE conversation_id = ?', (conversation_id,))
        connection.execute('DELETE FROM conversations WHERE user_id = ? AND id = ?', (user_id, conversation_id))


def authenticate_user(email: str, password: str) -> dict[str, Any]:
    email = validate_email(email)
    with _connection() as connection:
        row = connection.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if row is None or not password_context.verify(password, row['password_hash']):
        raise HTTPException(status_code=401, detail='Email or password is incorrect.')
    return get_user(int(row['id']))


def create_access_token(user_id: int, remember_me: bool = False) -> tuple[str, int]:
    expires_minutes = 30 * 24 * 60 if remember_me else settings.access_token_expire_minutes
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    token = jwt.encode({'sub': str(user_id), 'exp': expires_at}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_minutes * 60


def current_user(request: Request) -> dict[str, Any]:
    token = request.cookies.get(AUTH_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required.')
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get('sub', ''))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required.')
    return get_user(user_id)