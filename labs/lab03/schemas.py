"""Pydantic-моделі запитів і відповідей API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    """Модель для створення нової категорії."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str = Field(
        min_length=2,
        max_length=40,
        description="Унікальна назва категорії напряму аудиту (2-40 символів)",
        examples=["iam"],
    )


class CategoryRead(CategoryCreate):
    """Модель для читання категорії з ідентифікатором."""

    id: int = Field(gt=0, description="Унікальний ідентифікатор категорії")


class RecordCreate(BaseModel):
    """Модель для створення нового запису знахідки аудиту."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    code: str = Field(
        min_length=3,
        max_length=40,
        description="Унікальний код запису (наприклад, V13-01)",
        examples=["V13-TEST"],
    )
    title: str = Field(
        min_length=3,
        max_length=120,
        description="Назва / опис знахідки аудиту (3-120 символів)",
        examples=["Знахідка хмарного аудиту"],
    )
    category_id: int = Field(
        gt=0,
        description="Ідентифікатор наявної категорії (додатне ціле число)",
        examples=[1],
    )
    value: float = Field(
        ge=0.0,
        le=10.0,
        allow_inf_nan=False,
        description="Навчальна оцінка ризику від 0.0 до 10.0",
        examples=[7.5],
    )
    status: Literal["new", "in_progress", "done"] = Field(
        description="Статус опрацювання знахідки",
        examples=["new"],
    )


class RecordReplace(RecordCreate):
    """Модель для повної заміни змінюваних полів запису (PUT)."""


class RecordRead(RecordCreate):
    """Модель для читання знахідки аудиту з ID та назвою категорії."""

    id: int = Field(gt=0, description="Унікальний ідентифікатор запису")
    category_name: str = Field(description="Назва категорії, отримана через JOIN")


class StudentInfo(BaseModel):
    """Модель інформації про студента."""

    student_name: str
    group_name: str
    variant_number: int


class PingResponse(BaseModel):
    """Модель статусу перевірки працездатності сервісу."""

    status: str
