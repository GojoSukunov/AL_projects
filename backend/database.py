
import sqlite3
from pathlib import Path
from datetime import datetime

# Определяем корневую папку проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Папка для базы данных
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Путь к SQLite
DB_PATH = DATA_DIR / "my_ai_lab.db"


def get_connection():
    """Создаёт подключение к базе данных."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Создаёт таблицы базы данных."""

    with get_connection() as conn:

        # Таблица проектов
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                project_type TEXT DEFAULT 'regular',
                result_text TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Таблица файлов
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                mime_type TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE SET NULL
            )
        """)

        # Таблица результатов распознавания CIFAR
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                filename TEXT NOT NULL,
                predicted_class TEXT NOT NULL,
                confidence REAL NOT NULL,
                second_class TEXT,
                second_confidence REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE SET NULL
            )
        """)
        # Таблица программ Code Studio
        conn.execute("""
            CREATE TABLE IF NOT EXISTS code_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'python',
                filename TEXT,
                code TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            )
        """)

        # Автоматически добавляем CIFAR-10,
        # если его ещё нет
        conn.execute("""
            INSERT INTO projects (
                title,
                description,
                project_type,
                created_at
            )
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM projects
                WHERE project_type = 'cifar'
            )
        """, (
            "CIFAR-10",
            "Нейросеть для распознавания изображений.",
            "cifar",
            datetime.now().isoformat(timespec="seconds")
        ))

    print("SQLite database initialized successfully!")


if __name__ == "__main__":
    init_db()
