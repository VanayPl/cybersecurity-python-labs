"""Головний модуль FastAPI-застосунку Лабораторної роботи №3.

Предметна область: Реєстр ризиків хмарної конфігурації (Варіант 13).
Одиниця вимірювання: score (0.0 - 10.0).
"""

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

# Додавання кореня репозиторію до sys.path для підтримки прямого запуску у VS Code
_ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from labs.lab03.config import SUBJECT_AREA, SUBJECT_DESCRIPTION, VALUE_UNIT
from labs.lab03.database import initialize_database
from labs.lab03.routers.categories import router as categories_router
from labs.lab03.routers.records import router as records_router
from labs.lab03.schemas import PingResponse, StudentInfo
from shared import student


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Життєвий цикл застосунку: ініціалізація таблиць БД при старті."""
    initialize_database()
    yield


app = FastAPI(
    title=f"Web API: {SUBJECT_AREA}",
    description=(
        f"{SUBJECT_DESCRIPTION}\n\n"
        f"**Одиниця вимірювання (unit):** `{VALUE_UNIT}` (діапазон 0.0 - 10.0).\n"
        f"**Студент:** {student.STUDENT_NAME}, група {student.GROUP_NAME}, "
        f"варіант {student.VARIANT_NUMBER}."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Підключення модульних маршрутизаторів
app.include_router(categories_router)
app.include_router(records_router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Автоматичний редирект з головної сторінки на інтерактивну документацію Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get(
    "/ping",
    response_model=PingResponse,
    summary="Перевірка доступності API",
    tags=["Службові"],
)
def ping() -> dict[str, str]:
    """Перевірити працездатність та доступність сервісу."""
    return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentInfo,
    summary="Отримати дані про студента",
    tags=["Службові"],
)
def get_student_info() -> dict[str, str | int]:
    """Повернути ПІБ, академічну групу та номер варіанта студента."""
    return {
        "student_name": student.STUDENT_NAME,
        "group_name": student.GROUP_NAME,
        "variant_number": student.VARIANT_NUMBER,
    }


if __name__ == "__main__":
    uvicorn.run("labs.lab03.main:app", host="127.0.0.1", port=8000, reload=True)
