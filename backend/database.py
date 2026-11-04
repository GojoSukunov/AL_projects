import os
import sqlite3
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL")

# Локально используется SQLite, на Render — PostgreSQL.
if not DATABASE_URL:
    DATA_DIR = Path(os.getenv("MY_AI_LAB_DATA_DIR", BASE_DIR / "data"))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "my_ai_lab.db"


class PostgresCursor:
    """Небольшая совместимость с SQLite-кодом проекта."""

    def __init__(self, cursor):
        self.cursor = cursor
        self._lastrowid = None

    @property
    def lastrowid(self):
        if self._lastrowid is None:
            row = self.cursor.fetchone()
            if row:
                self._lastrowid = row["id"]
        return self._lastrowid

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()


class PostgresConnection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, params=()):
        query = query.replace("?", "%s").strip()

        # PostgreSQL возвращает id новой записи через RETURNING.
        if query.upper().startswith("INSERT INTO") and "RETURNING" not in query.upper():
            query = query.rstrip(";") + " RETURNING id"

        cursor = self.connection.execute(query, params)
        return PostgresCursor(cursor)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def get_connection():
    """Создаёт подключение к PostgreSQL или локальной SQLite."""

    if DATABASE_URL:
        connection = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row,
            connect_timeout=10
        )
        return PostgresConnection(connection)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Создаёт таблицы в выбранной базе данных."""

    if not DATABASE_URL:
        with get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    project_type TEXT DEFAULT 'regular',
                    result_text TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    original_name TEXT NOT NULL,
                    stored_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    mime_type TEXT,
                    created_at TEXT NOT NULL,
                        file_data BLOB,
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                        ON DELETE CASCADE
                );
                

                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    filename TEXT NOT NULL,
                    predicted_class TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    second_class TEXT,
                    second_confidence REAL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS code_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    language TEXT DEFAULT 'python',
                    filename TEXT,
                    code TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                        ON DELETE CASCADE
                );
                        """)

            try:
                conn.execute("ALTER TABLE files ADD COLUMN file_data BLOB")
            except sqlite3.OperationalError:
                pass

            _insert_cifar_project(conn)
        print("SQLite database initialized successfully!")
        return

    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id BIGSERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                project_type TEXT DEFAULT 'regular',
                result_text TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                
                id BIGSERIAL PRIMARY KEY,
                project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                mime_type TEXT,
                created_at TEXT NOT NULL,
                file_data BYTEA
            )
        
        """)
        conn.execute("""
            ALTER TABLE files
            ADD COLUMN IF NOT EXISTS file_data BYTEA
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id BIGSERIAL PRIMARY KEY,
                project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
                filename TEXT NOT NULL,
                predicted_class TEXT NOT NULL,
                confidence DOUBLE PRECISION NOT NULL,
                second_class TEXT,
                second_confidence DOUBLE PRECISION,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS code_files (
                id BIGSERIAL PRIMARY KEY,
                project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                language TEXT DEFAULT 'python',
                filename TEXT,
                code TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        _insert_cifar_project(conn)
        conn.commit()
        print("PostgreSQL database initialized successfully!")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def _insert_cifar_project(conn):
    existing = conn.execute("""
        SELECT id FROM projects
        WHERE project_type = ?
        LIMIT 1
    """, ("cifar",)).fetchone()

    if not existing:
        conn.execute("""
            INSERT INTO projects (
                title, description, project_type, result_text, created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            "CIFAR-10",
            "Распознавание изображений с помощью нейронной сети",
            "cifar",
            "",
            __import__("datetime").datetime.now().isoformat(timespec="seconds")
        ))