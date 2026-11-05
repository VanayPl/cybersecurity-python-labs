"""Маршрути для роботи з категоріями аудиту."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response, status

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Категорії"])


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Отримати список усіх категорій",
    description="Повертає список категорій аудиту, відсортований за зростанням id.",
)
def list_categories() -> list[dict]:
    """Повернути всі зареєстровані категорії аудиту."""
    return repository.get_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нову категорію",
    description="Створює нову категорію напряму перевірки хмарної конфігурації.",
    responses={
        409: {"description": "Категорія з такою назвою вже існує"},
        422: {"description": "Помилка валідації вхідних даних"},
    },
)
def create_category(payload: CategoryCreate) -> dict:
    """Створити нову унікальну категорію."""
    try:
        return repository.create_category(name=payload.name)
    except repository.ConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except repository.RepositoryError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка сервера при збереженні категорії",
        ) from err


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити порожню категорію",
    description="Видаляє категорію за її ідентифікатором, якщо вона не містить записів.",
    responses={
        204: {"description": "Категорію успішно видалено (тіло відповіді порожнє)"},
        404: {"description": "Категорію з вказаним id не знайдено"},
        409: {"description": "Неможливо видалити непорожню категорію"},
        422: {"description": "Некоректний ідентифікатор категорії"},
    },
)
def delete_category(
    category_id: Annotated[
        int, Path(gt=0, description="Додатний ідентифікатор категорії")
    ],
) -> Response:
    """Видалити порожню категорію за id."""
    try:
        repository.delete_category(category_id=category_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
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
            detail="Внутрішня помилка сервера при видаленні категорії",
        ) from err
