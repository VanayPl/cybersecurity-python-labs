"""Модуль початкового заповнення бази даних навчальними даними з JSON."""

import json
import logging
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from pydantic import ValidationError

from labs.lab03.database import get_connection, initialize_database
from labs.lab03.schemas import CategoryRead, RecordCreate

logger = logging.getLogger(__name__)

SEED_FILE_PATH = Path(__file__).resolve().parent / "data" / "seed.json"


def seed_database() -> bool:
    """Завантажити початкові дані у порожню базу в межах однієї транзакції.

    Повертає True, якщо заповнення виконано або база вже заповнена,
    та False у випадку критичної помилки валідації чи порушення обмежень.
    """
    if not SEED_FILE_PATH.exists():
        logger.error("Файл початкових даних не знайдено: %s", SEED_FILE_PATH)
        print(f"Помилка: файл початкових даних {SEED_FILE_PATH} не існує.")
        return False

    try:
        content = json.loads(SEED_FILE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        logger.error("Помилка декодування JSON: %s", err)
        print(f"Помилка декодування JSON у файлі початкових даних: {err}")
        return False

    # Перевірка структури даних через Pydantic
    try:
        categories_raw = content.get("categories", [])
        records_raw = content.get("records", [])

        validated_categories = [CategoryRead.model_validate(c) for c in categories_raw]
        validated_records = [RecordCreate.model_validate(r) for r in records_raw]
    except ValidationError as err:
        logger.error("Помилка валідації початкових даних: %s", err)
        print(f"Помилка валідації початкових даних за схемою Pydantic:\n{err}")
        return False

    if len(validated_categories) != 3 or len(validated_records) != 8:
        print(
            f"Попередження: очікувалося 3 категорії та 8 записів, "
            f"знайдено {len(validated_categories)} категорій і {len(validated_records)} записів."
        )

    # Ініціалізація структури таблиць, якщо їх ще не створено
    initialize_database()

    with closing(get_connection()) as connection:
        # Перевірка, чи база вже містить дані
        cur = connection.execute("SELECT COUNT(*) FROM categories")
        cat_count = cur.fetchone()[0]
        cur = connection.execute("SELECT COUNT(*) FROM records")
        rec_count = cur.fetchone()[0]

        if cat_count > 0 or rec_count > 0:
            print(
                f"База даних уже непорожня (категорій: {cat_count}, записів: {rec_count}). "
                "Початкове заповнення скасовано, дані не змінювалися, дублікатів не створено."
            )
            return True

        # Заповнення в одній неподільній транзакції
        try:
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(c.id, c.name) for c in validated_categories],
                )
                connection.executemany(
                    """
                    INSERT INTO records (code, title, category_id, value, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            r.code,
                            r.title,
                            r.category_id,
                            r.value,
                            r.status,
                        )
                        for r in validated_records
                    ],
                )
            print(
                f"Успіх: базу даних успішно заповнено початковими даними "
                f"({len(validated_categories)} категорії, {len(validated_records)} записів) "
                f"в єдиній транзакції."
            )
            return True
        except sqlite3.IntegrityError as err:
            logger.error("Помилка цілісності під час посіву: %s", err)
            print(
                f"Помилка цілісності даних при заповненні бази: {err}. "
                "Усі зміни транзакції скасовано (rollback)."
            )
            return False
        except sqlite3.Error as err:
            logger.error("Помилка бази даних під час посіву: %s", err)
            print(
                f"Помилка бази даних SQLite: {err}. "
                "Усі зміни транзакції скасовано (rollback)."
            )
            return False


if __name__ == "__main__":
    success = seed_database()
    if not success:
        sys.exit(1)
