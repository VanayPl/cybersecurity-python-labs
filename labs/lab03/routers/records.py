"""Маршрути для роботи із записами знахідок аудиту."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException, Path, Query, Response, status

from labs.lab03 import repository
from labs.lab03.config import MAX_BATCH_SIZE, MAX_LIMIT, MAX_VALUE, MIN_VALUE
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter(prefix="/records", tags=["Записи"])


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Отримати список записів з фільтрами та пагінацією",
    description=(
        "Повертає вибірку знахідок хмарного аудиту з можливістю фільтрації "
        "за категорією, статусом, мінімальною оцінкою та пошуком підрядка у назві."
    ),
    responses={
        422: {"description": "Помилка валідації параметрів запиту"},
    },
)
def list_records(
    category_id: Annotated[
        int | None,
        Query(
            gt=0,
            description="Фільтр за ідентифікатором категорії (тільки додатні числа)",
        ),
    ] = None,
    status_filter: Annotated[
        Literal["new", "in_progress", "done"] | None,
        Query(alias="status", description="Фільтр за статусом опрацювання знахідки"),
    ] = None,
    min_value: Annotated[
        float | None,
        Query(
            ge=MIN_VALUE,
            le=MAX_VALUE,
            description="Мінімальна оцінка ризику знахідки (від 0.0 до 10.0)",
        ),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=120,
            description="Буквальний підрядок у назві знахідки (case-sensitive)",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=MAX_LIMIT,
            description="Максимальна кількість записів у відповіді (1-100)",
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Кількість записів для пропуску (зсув)",
        ),
    ] = 0,
) -> list[dict]:
    """Отримати відфільтрований список записів знахідок аудиту."""
    return repository.get_records(
        category_id=category_id,
        status=status_filter,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати один запис за ідентифікатором",
    description="Повертає повну інформацію про знахідку аудиту за її ідентифікатором.",
    responses={
        404: {"description": "Запис не знайдено"},
        422: {"description": "Некоректний ідентифікатор запису"},
    },
)
def get_record(
    record_id: Annotated[int, Path(gt=0, description="Додатний ідентифікатор запису")],
) -> dict:
    """Повернути один запис за його id."""
    try:
        return repository.get_record_by_id(record_id=record_id)
    except repository.NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий запис",
    description="Додає нову знахідку аудиту до бази даних.",
    responses={
        201: {"description": "Запис успішно створено"},
        404: {"description": "Категорію з вказаним category_id не знайдено"},
        409: {"description": "Запис із таким кодом вже існує"},
        422: {"description": "Помилка валідації вхідних даних"},
    },
)
def create_record(payload: RecordCreate) -> dict:
    """Створити новий запис аудиту."""
    try:
        return repository.create_record(
            code=payload.code,
            title=payload.title,
            category_id=payload.category_id,
            value=payload.value,
            status=payload.status,
        )
    except repository.NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except repository.ConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except repository.RepositoryError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка сервера при збереженні запису",
        ) from err


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити змінювані поля наявного запису",
    description=(
        "Оновлює всі змінювані поля знахідки аудиту. "
        "Ідентифікатор запису залишається незмінним."
    ),
    responses={
        200: {"description": "Запис успішно оновлено"},
        404: {"description": "Запис або категорію не знайдено"},
        409: {"description": "Код запису конфліктує з іншим наявним записом"},
        422: {"description": "Помилка валідації вхідних даних або некоректний id"},
    },
)
def replace_record(
    record_id: Annotated[int, Path(gt=0, description="Додатний ідентифікатор запису")],
    payload: RecordReplace,
) -> dict:
    """Повністю замінити поля запису за id."""
    try:
        return repository.update_record(
            record_id=record_id,
            code=payload.code,
            title=payload.title,
            category_id=payload.category_id,
            value=payload.value,
            status=payload.status,
        )
    except repository.NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except repository.ConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except repository.RepositoryError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка сервера при оновленні запису",
        ) from err


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    description="Видаляє знахідку аудиту за її ідентифікатором.",
    responses={
        204: {"description": "Запис успішно видалено (тіло відповіді порожнє)"},
        404: {"description": "Запис із вказаним id не знайдено"},
        422: {"description": "Некоректний ідентифікатор запису"},
    },
)
def delete_record(
    record_id: Annotated[int, Path(gt=0, description="Додатний ідентифікатор запису")],
) -> Response:
    """Видалити запис аудиту за id."""
    try:
        repository.delete_record(record_id=record_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except repository.NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except repository.RepositoryError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка сервера при видаленні запису",
        ) from err


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Пакетне створення записів з атомарним збереженням",
    description=(
        "Приймає JSON-масив від 1 до 100 об'єктів RecordCreate та зберігає "
        "їх у межах однієї транзакції. При будь-якій помилці жоден запис не зберігається."
    ),
    responses={
        201: {"description": "Усі записи успішно створено в транзакції"},
        404: {"description": "Категорію для одного із записів не знайдено"},
        409: {
            "description": "Дублікат коду в базі даних або всередині переданого пакета"
        },
        422: {"description": "Помилка валідації пакета або його елементів"},
    },
)
def bulk_create_records(
    payload: Annotated[
        list[RecordCreate],
        Body(
            min_length=1,
            max_length=MAX_BATCH_SIZE,
            description="Масив записів для створення (від 1 до 100 елементів)",
        ),
    ],
) -> list[dict]:
    """Пакетно створити записи в єдиній транзакції."""
    try:
        records_raw = [item.model_dump() for item in payload]
        return repository.create_records_bulk(records_raw)
    except repository.NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except repository.ConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except repository.RepositoryError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка сервера під час пакетного створення",
        ) from err
