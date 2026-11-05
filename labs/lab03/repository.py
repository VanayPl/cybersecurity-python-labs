"""Шар доступу до даних (Repository) з параметризованими SQL-запитами.

Цей модуль не залежить від FastAPI та керує транзакціями SQLite.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import closing
from typing import Any

from labs.lab03.database import get_connection

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Базовий клас помилок репозиторію."""


class NotFoundError(RepositoryError):
    """Помилка: запис або пов'язану сутність не знайдено."""


class ConflictError(RepositoryError):
    """Помилка: конфлікт унікальності або обмеження цілісності."""


def get_categories() -> list[dict[str, Any]]:
    """Отримати список усіх категорій, відсортований за id."""
    with closing(get_connection()) as connection:
        cursor = connection.execute("SELECT id, name FROM categories ORDER BY id ASC")
        rows = cursor.fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]


def get_category_by_id(category_id: int) -> dict[str, Any] | None:
    """Отримати категорію за її ідентифікатором."""
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "SELECT id, name FROM categories WHERE id = ?",
            (category_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"id": row[0], "name": row[1]}


def create_category(name: str) -> dict[str, Any]:
    """Створити нову категорію."""
    with closing(get_connection()) as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name) VALUES (?)",
                    (name,),
                )
                category_id = cursor.lastrowid
                return {"id": category_id, "name": name}
        except sqlite3.IntegrityError as err:
            logger.warning("Конфлікт при створенні категорії '%s': %s", name, err)
            raise ConflictError(f"Категорія з назвою '{name}' вже існує") from err
        except sqlite3.Error as err:
            logger.error("Помилка БД при створенні категорії: %s", err)
            raise RepositoryError("Помилка бази даних") from err


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію за id.

    Якщо категорія містить записи або не існує, викидає відповідний виняток.
    """
    with closing(get_connection()) as connection:
        # Перевірка наявності категорії
        cur = connection.execute(
            "SELECT id FROM categories WHERE id = ?",
            (category_id,),
        )
        if cur.fetchone() is None:
            raise NotFoundError(f"Категорію з id={category_id} не знайдено")

        # Перевірка, чи категорія не містить записів
        cur = connection.execute(
            "SELECT COUNT(*) FROM records WHERE category_id = ?",
            (category_id,),
        )
        count = cur.fetchone()[0]
        if count > 0:
            raise ConflictError(
                f"Неможливо видалити категорію з id={category_id}, "
                f"оскільки вона містить {count} запис(ів)"
            )

        try:
            with connection:
                connection.execute(
                    "DELETE FROM categories WHERE id = ?",
                    (category_id,),
                )
        except sqlite3.IntegrityError as err:
            logger.warning("Порушення цілісності при видаленні категорії: %s", err)
            raise ConflictError(
                f"Неможливо видалити категорію з id={category_id}"
            ) from err
        except sqlite3.Error as err:
            logger.error("Помилка БД при видаленні категорії: %s", err)
            raise RepositoryError("Помилка бази даних") from err


def get_record_by_id(record_id: int) -> dict[str, Any]:
    """Отримати окремий запис за id разом із назвою категорії."""
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """
            SELECT r.id, r.code, r.title, r.category_id, r.value, r.status,
                   c.name AS category_name
            FROM records r
            JOIN categories c ON r.category_id = c.id
            WHERE r.id = ?
            """,
            (record_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise NotFoundError(f"Запис із id={record_id} не знайдено")

        return {
            "id": row[0],
            "code": row[1],
            "title": row[2],
            "category_id": row[3],
            "value": row[4],
            "status": row[5],
            "category_name": row[6],
        }


def get_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Отримати список записів із параметризованою фільтрацією та пагінацією."""
    with closing(get_connection()) as connection:
        query = (
            "SELECT r.id, r.code, r.title, r.category_id, r.value, r.status, "
            "c.name AS category_name "
            "FROM records r "
            "JOIN categories c ON r.category_id = c.id"
        )
        clauses: list[str] = []
        params: list[Any] = []

        if category_id is not None:
            clauses.append("r.category_id = ?")
            params.append(category_id)

        if status is not None:
            clauses.append("r.status = ?")
            params.append(status)

        if min_value is not None:
            clauses.append("r.value >= ?")
            params.append(min_value)

        if q is not None:
            clauses.append("instr(r.title, ?) > 0")
            params.append(q)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = connection.execute(query, tuple(params))
        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "code": row[1],
                "title": row[2],
                "category_id": row[3],
                "value": row[4],
                "status": row[5],
                "category_name": row[6],
            }
            for row in rows
        ]


def create_record(
    code: str,
    title: str,
    category_id: int,
    value: float,
    status: str,
) -> dict[str, Any]:
    """Створити новий запис із перевіркою існування категорії та унікальності коду."""
    with closing(get_connection()) as connection:
        # Перевірка існування категорії
        cur = connection.execute(
            "SELECT name FROM categories WHERE id = ?",
            (category_id,),
        )
        cat_row = cur.fetchone()
        if cat_row is None:
            raise NotFoundError(f"Категорію з id={category_id} не знайдено")
        category_name = cat_row[0]

        # Перевірка унікальності коду
        cur = connection.execute(
            "SELECT id FROM records WHERE code = ?",
            (code,),
        )
        if cur.fetchone() is not None:
            raise ConflictError(f"Запис із кодом '{code}' вже існує")

        try:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO records (code, title, category_id, value, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (code, title, category_id, value, status),
                )
                record_id = cursor.lastrowid
        except sqlite3.IntegrityError as err:
            logger.warning("Конфлікт при створенні запису: %s", err)
            raise ConflictError(f"Порушення обмежень цілісності: {err}") from err
        except sqlite3.Error as err:
            logger.error("Помилка БД при створенні запису: %s", err)
            raise RepositoryError("Помилка бази даних") from err

        return {
            "id": record_id,
            "code": code,
            "title": title,
            "category_id": category_id,
            "value": value,
            "status": status,
            "category_name": category_name,
        }


def update_record(
    record_id: int,
    code: str,
    title: str,
    category_id: int,
    value: float,
    status: str,
) -> dict[str, Any]:
    """Повністю замінити змінювані поля наявного запису (PUT)."""
    with closing(get_connection()) as connection:
        # Перевірка наявності запису
        cur = connection.execute(
            "SELECT id FROM records WHERE id = ?",
            (record_id,),
        )
        if cur.fetchone() is None:
            raise NotFoundError(f"Запис із id={record_id} не знайдено")

        # Перевірка наявності категорії
        cur = connection.execute(
            "SELECT name FROM categories WHERE id = ?",
            (category_id,),
        )
        cat_row = cur.fetchone()
        if cat_row is None:
            raise NotFoundError(f"Категорію з id={category_id} не знайдено")
        category_name = cat_row[0]

        # Перевірка унікальності коду для інших записів
        cur = connection.execute(
            "SELECT id FROM records WHERE code = ? AND id != ?",
            (code, record_id),
        )
        if cur.fetchone() is not None:
            raise ConflictError(f"Запис із кодом '{code}' вже існує під іншим id")

        try:
            with connection:
                connection.execute(
                    """
                    UPDATE records
                    SET code = ?, title = ?, category_id = ?, value = ?, status = ?
                    WHERE id = ?
                    """,
                    (code, title, category_id, value, status, record_id),
                )
        except sqlite3.IntegrityError as err:
            logger.warning("Конфлікт при оновленні запису id=%d: %s", record_id, err)
            raise ConflictError("Порушення обмежень цілісності") from err
        except sqlite3.Error as err:
            logger.error("Помилка БД при оновленні запису: %s", err)
            raise RepositoryError("Помилка бази даних") from err

        return {
            "id": record_id,
            "code": code,
            "title": title,
            "category_id": category_id,
            "value": value,
            "status": status,
            "category_name": category_name,
        }


def delete_record(record_id: int) -> None:
    """Видалити запис за його ідентифікатором."""
    with closing(get_connection()) as connection:
        cur = connection.execute(
            "SELECT id FROM records WHERE id = ?",
            (record_id,),
        )
        if cur.fetchone() is None:
            raise NotFoundError(f"Запис із id={record_id} не знайдено")

        try:
            with connection:
                connection.execute(
                    "DELETE FROM records WHERE id = ?",
                    (record_id,),
                )
        except sqlite3.Error as err:
            logger.error("Помилка БД при видаленні запису id=%d: %s", record_id, err)
            raise RepositoryError("Помилка бази даних") from err


def create_records_bulk(
    records_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Пакетне створення записів в одній неподільній транзакції (атомарно).

    Якщо хоча б один елемент некоректний (дублікат коду в базі чи всередині
    пакета, неіснуюча категорія тощо) — жоден запис не зберігається.
    """
    if not records_data:
        return []

    # 1. Перевірка внутрішніх дублікатів коду в пакеті
    codes_in_batch: set[str] = set()
    for item in records_data:
        code = item["code"]
        if code in codes_in_batch:
            raise ConflictError(f"Дублікат коду '{code}' всередині переданого пакета")
        codes_in_batch.add(code)

    with closing(get_connection()) as connection:
        # 2. Перевірка існування всіх категорій, на які є посилання
        category_ids = {item["category_id"] for item in records_data}
        placeholders = ",".join("?" for _ in category_ids)
        cur = connection.execute(
            f"SELECT id, name FROM categories WHERE id IN ({placeholders})",
            tuple(category_ids),
        )
        found_cats = {row[0]: row[1] for row in cur.fetchall()}
        missing_cats = category_ids - set(found_cats.keys())
        if missing_cats:
            missing_id = min(missing_cats)
            raise NotFoundError(f"Категорію з id={missing_id} не знайдено в базі даних")

        # 3. Перевірка колізії коду з уже наявними в базі записами
        code_placeholders = ",".join("?" for _ in codes_in_batch)
        cur = connection.execute(
            f"SELECT code FROM records WHERE code IN ({code_placeholders})",
            tuple(codes_in_batch),
        )
        existing_row = cur.fetchone()
        if existing_row is not None:
            raise ConflictError(
                f"Запис із кодом '{existing_row[0]}' вже існує в базі даних"
            )

        # 4. Атомарне виконання всіх вставок в одній транзакції
        created_records: list[dict[str, Any]] = []
        try:
            with connection:
                for item in records_data:
                    cursor = connection.execute(
                        """
                        INSERT INTO records (code, title, category_id, value, status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            item["code"],
                            item["title"],
                            item["category_id"],
                            item["value"],
                            item["status"],
                        ),
                    )
                    rec_id = cursor.lastrowid
                    created_records.append(
                        {
                            "id": rec_id,
                            "code": item["code"],
                            "title": item["title"],
                            "category_id": item["category_id"],
                            "value": item["value"],
                            "status": item["status"],
                            "category_name": found_cats[item["category_id"]],
                        }
                    )
        except sqlite3.IntegrityError as err:
            logger.warning("Порушення цілісності при пакетній вставці: %s", err)
            raise ConflictError(
                f"Порушення цілісності даних при пакетній вставці: {err}"
            ) from err
        except sqlite3.Error as err:
            logger.error("Помилка БД при пакетній вставці: %s", err)
            raise RepositoryError("Помилка бази даних під час транзакції") from err

        return created_records
