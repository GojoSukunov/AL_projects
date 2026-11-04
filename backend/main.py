
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pathlib import Path
from PIL import Image
from io import BytesIO
from datetime import datetime
import uuid
import os

import torch
import numpy as np

from backend.model import load_model
from backend.database import get_connection, init_db


app = FastAPI(
    title="MY AI LAB",
    description="Personal AI Laboratory",
    version="1.0.0"
)


class ProjectCreate(BaseModel):
    title: str
    description: str = ""
# Создание программы Code Studio
class CodeCreate(BaseModel):
    project_id: int
    title: str
    language: str = "python"
    filename: str = ""
    code: str = ""


# Редактирование программы Code Studio
class CodeUpdate(BaseModel):
    title: str
    language: str = "python"
    filename: str = ""
    code: str = ""


@app.post("/api/projects")
def create_project(project: ProjectCreate):

    title = project.title.strip()
    description = project.description.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Название проекта обязательно"
        )

    conn = get_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO projects (
                title,
                description,
                project_type,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            title,
            description,
            "regular",
            datetime.now().isoformat(timespec="seconds")
        ))

        conn.commit()

        new_project = conn.execute("""
            SELECT *
            FROM projects
            WHERE id = ?
        """, (cursor.lastrowid,)).fetchone()

        return dict(new_project)

    finally:
        conn.close()


# Редактирование проекта
@app.put("/api/projects/{project_id}")
def update_project(project_id: int, project: ProjectCreate):

    title = project.title.strip()
    description = project.description.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Название проекта обязательно"
        )

    conn = get_connection()

    try:
        # Проверяем существование проекта
        existing_project = conn.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        ).fetchone()

        if not existing_project:
            raise HTTPException(
                status_code=404,
                detail="Проект не найден"
            )

        # Защищаем системный проект CIFAR-10
        if existing_project["project_type"] == "cifar":
            raise HTTPException(
                status_code=403,
                detail="Системный проект CIFAR-10 нельзя редактировать"
            )

        # Обновляем данные
        conn.execute("""
            UPDATE projects
            SET title = ?, description = ?
            WHERE id = ?
        """, (
            title,
            description,
            project_id
        ))

        conn.commit()

        updated_project = conn.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        ).fetchone()

        return dict(updated_project)

    finally:
        conn.close()


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Папка для загруженных изображений и документов


UPLOAD_DIR = Path(
    os.getenv("MY_AI_LAB_UPLOAD_DIR", BASE_DIR / "uploads")
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Разрешённые форматы
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp"
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация базы данных
@app.on_event("startup")
def startup():
    init_db()


# Загружаем модель один раз при запуске сервера
cifar_model, device = load_model()

CLASSES = [
    "Самолёт",
    "Автомобиль",
    "Птица",
    "Кошка",
    "Олень",
    "Собака",
    "Лягушка",
    "Лошадь",
    "Корабль",
    "Грузовик"
]


@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "name": "MY AI LAB",
        "database": "PostgreSQL" if os.getenv("DATABASE_URL") else "SQLite"
    }


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


# Получение списка проектов

# Получение списка проектов
@app.get("/api/projects")
def get_projects():
    conn = get_connection()

    try:
        projects = conn.execute("""
            SELECT *
            FROM projects
            ORDER BY created_at DESC
        """).fetchall()

        return [dict(project) for project in projects]

    finally:
        conn.close()


# ======================================
# CODE STUDIO
# ======================================

# Создание программы
@app.post("/api/code")
def create_code(item: CodeCreate):
    title = item.title.strip()
    language = item.language.strip().lower()
    filename = item.filename.strip()

    if not title:
        raise HTTPException(status_code=400, detail="Название программы обязательно")

    if not language:
        raise HTTPException(status_code=400, detail="Укажите язык программирования")

    conn = get_connection()

    try:
        project = conn.execute(
            "SELECT * FROM projects WHERE id = ?",
            (item.project_id,)
        ).fetchone()

        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        if project["project_type"] == "cifar":
            raise HTTPException(
                status_code=403,
                detail="Нельзя добавлять код в системный проект CIFAR-10"
            )

        now = datetime.now().isoformat(timespec="seconds")

        cursor = conn.execute("""
            INSERT INTO code_files (
                project_id, title, language, filename,
                code, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item.project_id, title, language, filename,
            item.code, now, now
        ))

        conn.commit()

        result = conn.execute(
            "SELECT * FROM code_files WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()

        return dict(result)

    finally:
        conn.close()


# Получение всех программ
@app.get("/api/code")
def get_all_code():
    conn = get_connection()

    try:
        codes = conn.execute("""
            SELECT
                code_files.*,
                projects.title AS project_title
            FROM code_files
            JOIN projects ON projects.id = code_files.project_id
            ORDER BY code_files.updated_at DESC
        """).fetchall()

        return [dict(item) for item in codes]

    finally:
        conn.close()


# Открытие конкретной программы
@app.get("/api/code/{code_id}")
def get_code(code_id: int):
    conn = get_connection()

    try:
        item = conn.execute("""
            SELECT
                code_files.*,
                projects.title AS project_title
            FROM code_files
            JOIN projects ON projects.id = code_files.project_id
            WHERE code_files.id = ?
        """, (code_id,)).fetchone()

        if not item:
            raise HTTPException(status_code=404, detail="Программа не найдена")

        return dict(item)

    finally:
        conn.close()


# Редактирование программы
@app.put("/api/code/{code_id}")
def update_code(code_id: int, item: CodeUpdate):
    title = item.title.strip()
    language = item.language.strip().lower()
    filename = item.filename.strip()

    if not title:
        raise HTTPException(status_code=400, detail="Название программы обязательно")

    if not language:
        raise HTTPException(status_code=400, detail="Укажите язык программирования")

    conn = get_connection()

    try:
        existing = conn.execute(
            "SELECT id FROM code_files WHERE id = ?",
            (code_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Программа не найдена")

        now = datetime.now().isoformat(timespec="seconds")

        conn.execute("""
            UPDATE code_files
            SET title = ?, language = ?, filename = ?,
                code = ?, updated_at = ?
            WHERE id = ?
        """, (
            title, language, filename,
            item.code, now, code_id
        ))

        conn.commit()

        updated = conn.execute(
            "SELECT * FROM code_files WHERE id = ?",
            (code_id,)
        ).fetchone()

        return dict(updated)

    finally:
        conn.close()


# Удаление программы
@app.delete("/api/code/{code_id}")
def delete_code(code_id: int):
    conn = get_connection()

    try:
        existing = conn.execute(
            "SELECT id FROM code_files WHERE id = ?",
            (code_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Программа не найдена")

        conn.execute(
            "DELETE FROM code_files WHERE id = ?",
            (code_id,)
        )

        conn.commit()

        return {"message": "Программа успешно удалена"}

    finally:
        conn.close()


# ======================================
# ФАЙЛЫ ПРОЕКТОВ
# ======================================

MAX_PROJECT_FILE_SIZE = 20 * 1024 * 1024  # 20 МБ

ALLOWED_PROJECT_FILES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".zip": "application/zip"
}




# Получение файлов конкретного проекта
@app.get("/api/projects/{project_id}/files")
def get_project_files(project_id: int):
    conn = get_connection()

    try:
        project = conn.execute(
            "SELECT id FROM projects WHERE id = ?",
            (project_id,)
        ).fetchone()

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Проект не найден"
            )

        files = conn.execute("""
            SELECT id, project_id, original_name, stored_name, mime_type, created_at
            FROM files
            WHERE project_id = ?
            ORDER BY created_at DESC
        """, (project_id,)).fetchall()

        result = []

        for item in files:
            file_data = dict(item)

            # Получаем размер файла
            file_path = UPLOAD_DIR / item["stored_name"]

            file_data["size"] = (
                file_path.stat().st_size
                if file_path.is_file()
                else 0
            )

            # Ссылка для скачивания
            file_data["download_url"] = (
                f"/api/files/{item['id']}/download"
            )

            # Ссылка для просмотра изображения
            if item["mime_type"] and item["mime_type"].startswith("image/"):
                file_data["image_url"] = (
                    f"/api/files/{item['id']}/view"
                )

            result.append(file_data)

        return result

    finally:
        conn.close()


# Загрузка файла в проект
@app.post("/api/projects/{project_id}/files")
async def upload_project_file(project_id: int, file: UploadFile = File(...)):
    original_name = Path(file.filename or "file").name
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_PROJECT_FILES:
        raise HTTPException(
            status_code=400,
            detail="Этот формат файла не поддерживается"
        )

    contents = await file.read(MAX_PROJECT_FILE_SIZE + 1)

    if len(contents) > MAX_PROJECT_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Размер файла не должен превышать 20 МБ"
        )

    if not contents:
        raise HTTPException(status_code=400, detail="Файл пустой")

    stored_name = f"{uuid.uuid4().hex}{extension}"
    saved_path = UPLOAD_DIR / stored_name
    created_at = datetime.now().isoformat(timespec="seconds")
    mime_type = ALLOWED_PROJECT_FILES[extension]

    conn = get_connection()

    try:
        project = conn.execute(
            "SELECT id FROM projects WHERE id = ?",
            (project_id,)
        ).fetchone()

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Проект не найден"
            )

        # Проверяем, есть ли уже файл в проекте
        existing_file = conn.execute(
            "SELECT id FROM files WHERE project_id = ? LIMIT 1",
            (project_id,)
        ).fetchone()

        if existing_file:
            raise HTTPException(
                status_code=409,
                detail="В этом проекте уже есть файл. Сначала удалите его."
            )

        saved_path.write_bytes(contents)
        cursor = conn.execute("""
            INSERT INTO files (
                project_id,
                original_name,
                stored_name,
                file_path,
                mime_type,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            original_name,
            stored_name,
            f"uploads/{stored_name}",
            mime_type,
            created_at
        ))

        conn.commit()

        return {
            "id": cursor.lastrowid,
            "project_id": project_id,
            "original_name": original_name,
            "mime_type": mime_type,
            "created_at": created_at
        }

    except Exception:
        conn.rollback()

        if saved_path.exists():
            saved_path.unlink()

        raise

    finally:
        conn.close()


# Просмотр изображения прямо в браузере
@app.get("/api/files/{file_id}/view")
def view_project_file(file_id: int):
    return get_project_file_response(file_id, inline=True)


# Скачивание файла
@app.get("/api/files/{file_id}/download")
def download_project_file(file_id: int):
    return get_project_file_response(file_id, inline=False)


def get_project_file_response(file_id: int, inline: bool):
    from fastapi.responses import Response

    conn = get_connection()

    try:
        item = conn.execute(
            "SELECT * FROM files WHERE id = ?",
            (file_id,)
        ).fetchone()

        if not item:
            raise HTTPException(status_code=404, detail="Файл не найден")

        path = UPLOAD_DIR / item["stored_name"]

        if not path.is_file():
            raise HTTPException(status_code=404, detail="Файл отсутствует на диске")

        if inline:
            return FileResponse(
                path,
                media_type=item["mime_type"],
                headers={"Content-Disposition": "inline"}
            )

        return FileResponse(
            path,
            media_type=item["mime_type"],
            filename=item["original_name"]
        )

    finally:
        conn.close()


# История распознавания CIFAR
@app.get("/api/cifar/history")
def get_cifar_history():
    conn = get_connection()

    try:
        history = conn.execute("""
            SELECT *
            FROM predictions
            ORDER BY created_at DESC
        """).fetchall()

        return [dict(item) for item in history]

    finally:
        conn.close()


@app.post("/api/cifar/predict")
async def predict_image(file: UploadFile = File(...)):

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Загрузите изображение JPG, PNG или WEBP"
        )

    contents = await file.read()

    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Размер изображения не должен превышать 10 МБ"
        )

    saved_path = None

    try:
        # Обработка изображения
        image = Image.open(BytesIO(contents)).convert("RGB")
        image = image.resize(
            (32, 32),
            Image.Resampling.BILINEAR
        )

        # Аналог transforms.ToTensor()
        array = np.asarray(image, dtype=np.float32) / 255.0
        array = np.transpose(array, (2, 0, 1))

        tensor = torch.from_numpy(array).unsqueeze(0).to(device)

        with torch.no_grad():
            output = cifar_model(tensor)
            probabilities = torch.softmax(output, dim=1)[0]

        results = [
            {
                "class": CLASSES[i],
                "probability": round(
                    float(probabilities[i].item()) * 100, 2
                )
            }
            for i in range(len(CLASSES))
        ]

        results.sort(
            key=lambda item: item["probability"],
            reverse=True
        )

        prediction = results[0]
        second_prediction = results[1]

        # Сохраняем изображение
        stored_name = f"{uuid.uuid4().hex}{ALLOWED_TYPES[file.content_type]}"
        saved_path = UPLOAD_DIR / stored_name
        saved_path.write_bytes(contents)

        original_name = Path(file.filename or "image").name
        created_at = datetime.now().isoformat(timespec="seconds")

        # Сохраняем результат в SQLite
        conn = get_connection()

        try:
            project = conn.execute("""
                SELECT id
                FROM projects
                WHERE project_type = 'cifar'
                LIMIT 1
            """).fetchone()

            project_id = project["id"] if project else None

            cursor = conn.execute("""
                INSERT INTO files (
                    project_id,
                    original_name,
                    stored_name,
                    file_path,
                    mime_type,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                original_name,
                stored_name,
                f"uploads/{stored_name}",
                file.content_type,
                created_at
            ))

            conn.execute("""
                INSERT INTO predictions (
                    project_id,
                    filename,
                    predicted_class,
                    confidence,
                    second_class,
                    second_confidence,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                original_name,
                prediction["class"],
                prediction["probability"],
                second_prediction["class"],
                second_prediction["probability"],
                created_at
            ))

            conn.commit()

            file_id = cursor.lastrowid

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

        return {
            "prediction": prediction["class"],
            "confidence": prediction["probability"],
            "results": results,
            "file_id": file_id,
            "filename": original_name,
            "image_url": f"/uploads/{stored_name}",
            "created_at": created_at
        }

    except HTTPException:
        raise

    except Exception as error:
        if saved_path and saved_path.exists():
            saved_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=f"Не удалось обработать изображение: {str(error)}"
        )


# Доступ к сохранённым изображениям
app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads"
)

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)

@app.delete("/api/files/{file_id}")
def delete_project_file(file_id: int):
    conn = get_connection()

    try:
        item = conn.execute(
            "SELECT * FROM files WHERE id = ?",
            (file_id,)
        ).fetchone()

        if not item:
            raise HTTPException(status_code=404, detail="Файл не найден")


        path = UPLOAD_DIR / item["stored_name"]

        conn.execute(
            "DELETE FROM files WHERE id = ?",
            (file_id,)
        )
        conn.commit()

        if path.exists():
            path.unlink()

        return {"message": "Файл успешно удалён"}

    finally:
        conn.close()



@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int):
    conn = get_connection()

    try:
        # Находим проект
        project = conn.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        ).fetchone()

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Проект не найден"
            )

        # Запрещаем удалять системный проект CIFAR
        if project["project_type"] == "cifar":
            raise HTTPException(
                status_code=403,
                detail="Системный проект CIFAR-10 нельзя удалить"
            )

        # Получаем все файлы проекта
        files = conn.execute(
            "SELECT * FROM files WHERE project_id = ?",
            (project_id,)
        ).fetchall()

        # Удаляем записи о файлах
        conn.execute(
            "DELETE FROM files WHERE project_id = ?",
            (project_id,)
        )

        # Удаляем историю предсказаний проекта
        conn.execute(
            "DELETE FROM predictions WHERE project_id = ?",
            (project_id,)
        )

        # Удаляем проект
        conn.execute(
            "DELETE FROM projects WHERE id = ?",
            (project_id,)
        )

        conn.commit()

        # Удаляем физические файлы
        for item in files:
            path = UPLOAD_DIR / item["stored_name"]

            if path.is_file():
                path.unlink()

        return {
            "message": "Проект и его файлы успешно удалены"
        }

    finally:
        conn.close()
