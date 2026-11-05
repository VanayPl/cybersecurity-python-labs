# ЗВІТ
до лабораторної роботи №3
з курсу: «Програмування скриптовими мовами»
на тему: «Прикладні бібліотеки Python для побудови веб застосунків»
**Варіант №28 (13)**

**Виконав:** студент групи КБ-202 Якимчук І.І.  
**Прийняв:** Петрів П.П.  
**Місто:** Львів, 2026  

---

## Мета роботи
1. Навчитися створювати надійні та швидкодіючі Web API застосунки за допомогою сучасного фреймворку FastAPI, визначати маршрути для CRUD-операцій, групувати ендпоінти через APIRouter та користуватися автоматично генерованою інтерактивною документацією Swagger UI (`/docs`) та OpenAPI.
2. Опанувати створення реляційних баз даних SQLite без використання ORM (безпосередньо через вбудований модуль `sqlite3`), виконання SQL-операцій із безпечними параметризованими запитами для повного унеможливлення ризику SQL-ін'єкцій, використання зовнішніх ключів (`PRAGMA foreign_keys = ON`) та обмежень цілісності `NOT NULL`, `UNIQUE`, `CHECK`.
3. Навчитися здійснювати сувору перевірку вхідних даних за допомогою Pydantic v2 (обмеження типів, довжини, числових меж, дозволених статусів, `extra="forbid"`), формувати відповідні моделі відповідей (`response_model`), централізовано обробляти помилки (`HTTPException`) та виконувати пов'язані пакети змін в атомарних межах однієї транзакції.

---

## Індивідуальне завдання (Варіант 28 (13))
Відповідно до номера за списком групи (28) та правила циклічного розрахунку варіантів з 15 наявних у методичних вказівках ((28 - 1) % 15 + 1 = 13), індивідуальним завданням є **Варіант 13: «Реєстр ризиків хмарної конфігурації»**.

- **Предметна область:** Розробка сервісу обліку знахідок аудиту хмарної конфігурації (Cloud Security Configuration Risks Registry). Категорія визначає напрям аудиторської перевірки (`iam`, `storage`, `network`), `value` — навчальну оцінку ризику від 0.0 до 10.0, `status` — поточний стан опрацювання знахідки (`new`, `in_progress`, `done`).
- **Категорії (id: 1, 2, 3):** `iam`, `storage`, `network`.
- **Назва запису для генерації назв знахідок (title):** «Знахідка хмарного аудиту».
- **Прикладний поріг реагування (threshold):** 7.0 (одиниця вимірювання unit = `"score"`).
- **Навчальні значення (value):** `[8.0, 6.5, 4.0, 9.0, 7.5, 3.0, 7.0, 5.0]`.
- **Обмеження на числові поля:** значення `value` є числом з плаваючою крапкою (`REAL` / `float`) у діапазоні від 0.0 до 10.0 включно. Нескінченні величини та NaN суворо відхиляються валідатором Pydantic (`allow_inf_nan=False`).

### Комплекс завдань:
1. **Завдання 1: SQLite-база та шар доступу до даних.** Створення схеми таблиць за готовим DDL-скриптом `schema.sql`, реалізація фабрики з'єднань з контролем зовнішніх ключів `database.py`, створення модуля початкового атомарного посіву з валідацією JSON `seed.py`, розробка шару репозиторію `repository.py` з чистими параметризованими SQL-запитами, пагінацією та безпечним транзакційним пакетом.
2. **Завдання 2: Web API за допомогою FastAPI.** Побудова REST API застосунку в `main.py`, налаштування APIRouter для модулів `routers/categories.py` та `routers/records.py`, розробка Pydantic-моделей `schemas.py`, реалізація ендпоінтів `/ping`, `/student`, повного набору CRUD для категорій та записів, фільтрів (`category_id`, `status`, `min_value`, `q`, `limit`, `offset`) та атомарного методу `POST /records/bulk`.
3. **Завдання 3: Перевірка API, збереження даних і транзакцій.** Комплексне тестування 14 обов'язкових сценаріїв з перевіркою коректності HTTP-відповідей (200, 201, 204, 404, 409, 422), стійкості до SQL-ін'єкцій, персистентності на диску та атомарного відкату транзакцій при спробі зберегти некоректний пакет.

---

## Хід виконання роботи

1. **Підготовка структури репозиторію та оточення:**
   У корені репозиторію `cybersecurity-python-labs` додано пакет `labs/lab03/` з підпакетом `routers/` та каталогом `data/`. Встановлено та зафіксовано в `requirements.txt` бібліотеки `fastapi`, `uvicorn`, `pydantic` та `ruff`. Модуль `shared/student.py` налаштовано на дані студента. У `.gitignore` додано виключення для тимчасових файлів SQLite (`*.sqlite3`, `*.db`).
2. **Створення схеми та бази даних SQLite (schema.sql, database.py):**
   Налаштовано з'єднання з базою даних через контекстний менеджер `get_connection()` із примусовим виконанням директиви `PRAGMA foreign_keys = ON;`. Створено таблиці `categories` та `records` із зовнішнім ключем `FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT`.
3. **Початковий посів даних (data/seed.json, seed.py):**
   Створено JSON-файл із трьома категоріями та вісьмома навчальними записами для Варіанта 13. У `seed.py` реалізовано попередню валідацію через моделі Pydantic та атомарне вставлення даних в одній неподільній транзакції `with connection:`. Реалізовано захист від дублювання при повторних запусках скрипту.
4. **Шар доступу до даних (repository.py):**
   Реалізовано функції взаємодії з БД без використання ORM. Всі параметри передаються виключно через кортежі плейсхолдерів `?`. Забезпечено трансляцію помилок `sqlite3.IntegrityError` у доменні класи `NotFoundError` та `ConflictError`. Пошук підрядка реалізовано через безпечну функцію `instr(title, ?) > 0`.
5. **Розробка API (main.py, routers/categories.py, routers/records.py):**
   Створено застосунок FastAPI з підключенням життєвого циклу `lifespan` для автоініціалізації БД. Реалізовано всі обов'язкові маршрути, параметри фільтрації, пагінацію та сувору Pydantic-валідацію (`extra="forbid"`, `allow_inf_nan=False`).
6. **Тестування та перевірка коду через Ruff:**
   Код перевірено лінтером та форматтером `ruff`. Усі тести та сценарії пройшли зі 100% успішністю.

---

## Лістинги коду основних модулів

### Лістинг 1. Схема бази даних (labs/lab03/schema.sql)
```sql
PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL UNIQUE
        CHECK (length(trim(name)) BETWEEN 2 AND 40)
);

CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    code TEXT NOT NULL UNIQUE
        CHECK (length(trim(code)) BETWEEN 3 AND 40),
    title TEXT NOT NULL
        CHECK (length(trim(title)) BETWEEN 3 AND 120),
    category_id INTEGER NOT NULL
        CHECK (typeof(category_id) = 'integer' AND category_id > 0),
    value REAL NOT NULL
        CHECK (typeof(value) IN ('integer', 'real')
            AND value BETWEEN 0 AND 10),
    status TEXT NOT NULL
        CHECK (status IN ('new', 'in_progress', 'done')),
    FOREIGN KEY (category_id) REFERENCES categories(id)
        ON DELETE RESTRICT
);

COMMIT;
```

### Лістинг 2. Конфігурація варіанта (labs/lab03/config.py)
```python
"""Конфігурація та константи варіанта (Варіант 13: Реєстр ризиків хмарної конфігурації)."""

SUBJECT_AREA: str = "Реєстр ризиків хмарної конфігурації"
SUBJECT_DESCRIPTION: str = (
    "Сервіс обліку знахідок аудиту хмарної конфігурації. "
    "Категорія визначає напрям перевірки (iam, storage, network), "
    "value — навчальну оцінку ризику від 0.0 до 10.0, "
    "status — стан опрацювання знахідки."
)
VALUE_UNIT: str = "score"
THRESHOLD: float = 7.0
MIN_VALUE: float = 0.0
MAX_VALUE: float = 10.0

ALLOWED_CATEGORIES: tuple[str, ...] = ("iam", "storage", "network")
ALLOWED_STATUSES: tuple[str, ...] = ("new", "in_progress", "done")
RECORD_TITLE_PREFIX: str = "Знахідка хмарного аудиту"

DEFAULT_LIMIT: int = 20
MAX_LIMIT: int = 100
MAX_BATCH_SIZE: int = 100
```

### Лістинг 3. Підключення до БД (labs/lab03/database.py)
```python
import sqlite3
from contextlib import closing
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "lab3.sqlite3"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Відкрити з’єднання з перевіркою зовнішніх ключів."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
    except sqlite3.Error:
        connection.close()
        raise


def initialize_database() -> None:
    """Створити таблиці за готовим SQL-скриптом."""
    script = SCHEMA_PATH.read_text(encoding="utf-8")
    with closing(get_connection()) as connection:
        try:
            connection.executescript(script)
        except sqlite3.Error:
            connection.rollback()
            raise


if __name__ == "__main__":
    initialize_database()
```

### Лістинг 4. Pydantic-моделі валідації (labs/lab03/schemas.py)
```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=2, max_length=40, examples=["iam"])


class CategoryRead(CategoryCreate):
    id: int = Field(gt=0)


class RecordCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    code: str = Field(min_length=3, max_length=40, examples=["V13-TEST"])
    title: str = Field(
        min_length=3, max_length=120, examples=["Знахідка хмарного аудиту"]
    )
    category_id: int = Field(gt=0, examples=[1])
    value: float = Field(ge=0.0, le=10.0, allow_inf_nan=False, examples=[7.5])
    status: Literal["new", "in_progress", "done"] = Field(examples=["new"])


class RecordReplace(RecordCreate):
    pass


class RecordRead(RecordCreate):
    id: int = Field(gt=0)
    category_name: str


class StudentInfo(BaseModel):
    student_name: str
    group_name: str
    variant_number: int


class PingResponse(BaseModel):
    status: str
```

### Лістинг 5. Модуль посіву навчальних даних (labs/lab03/seed.py)
```python
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
    if not SEED_FILE_PATH.exists():
        return False
    try:
        content = json.loads(SEED_FILE_PATH.read_text(encoding="utf-8"))
        validated_categories = [
            CategoryRead.model_validate(c) for c in content.get("categories", [])
        ]
        validated_records = [
            RecordCreate.model_validate(r) for r in content.get("records", [])
        ]
    except (json.JSONDecodeError, ValidationError) as err:
        logger.error("Validation error: %s", err)
        return False

    initialize_database()

    with closing(get_connection()) as connection:
        cat_count = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        rec_count = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]

        if cat_count > 0 or rec_count > 0:
            print(
                f"База даних уже непорожня (категорій: {cat_count}, записів: {rec_count}). Початкове заповнення скасовано, дані не змінювалися, дублікатів не створено."
            )
            return True

        try:
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(c.id, c.name) for c in validated_categories],
                )
                connection.executemany(
                    "INSERT INTO records (code, title, category_id, value, status) VALUES (?, ?, ?, ?, ?)",
                    [
                        (r.code, r.title, r.category_id, r.value, r.status)
                        for r in validated_records
                    ],
                )
            print(
                f"Успіх: базу даних успішно заповнено початковими даними ({len(validated_categories)} категорії, {len(validated_records)} записів) в єдиній транзакції."
            )
            return True
        except sqlite3.Error as err:
            logger.error("DB error during seed: %s", err)
            return False


if __name__ == "__main__":
    if not seed_database():
        sys.exit(1)
```

### Лістинг 6. Головний модуль FastAPI (labs/lab03/main.py)
```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI

from labs.lab03.config import SUBJECT_AREA, SUBJECT_DESCRIPTION, VALUE_UNIT
from labs.lab03.database import initialize_database
from labs.lab03.routers.categories import router as categories_router
from labs.lab03.routers.records import router as records_router
from labs.lab03.schemas import PingResponse, StudentInfo
from shared import student


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    initialize_database()
    yield


app = FastAPI(
    title=f"Web API: {SUBJECT_AREA}",
    description=f"{SUBJECT_DESCRIPTION}\n\n**Одиниця вимірювання (unit):** `{VALUE_UNIT}` (діапазон 0.0 - 10.0).\n**Студент:** {student.STUDENT_NAME}, група {student.GROUP_NAME}, варіант {student.VARIANT_NUMBER}.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(categories_router)
app.include_router(records_router)


@app.get(
    "/ping",
    response_model=PingResponse,
    summary="Перевірка доступності API",
    tags=["Службові"],
)
def ping() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentInfo,
    summary="Отримати дані про студента",
    tags=["Службові"],
)
def get_student_info() -> dict[str, str | int]:
    return {
        "student_name": student.STUDENT_NAME,
        "group_name": student.GROUP_NAME,
        "variant_number": student.VARIANT_NUMBER,
    }
```

---

## Результати виконання обов'язкових сценаріїв (Завдання 3)

| № | Сценарій | Метод та URL | Очікуваний HTTP-код | Фактичний результат |
|---|---|---|---|---|
| 1 | Початковий посів та повторний запуск | `python -m labs.lab03.seed` | - | Заповнено 3 категорії, 8 записів; повторний запуск не змінює базу і не створює дублікатів |
| 2 | Службові маршрути | `GET /ping`, `/student`, `/categories` | 200 | Повернуто статус `ok`, ПІБ студента, групу, варіант 13 та 3 категорії |
| 3 | Життєвий цикл окремого запису | `POST /records` -> `GET /records/9` -> `PUT /records/9` -> `DELETE /records/9` | 201 -> 200 -> 200 -> 204 (наступний GET дає 404) | Повний цикл CRUD успішно пройдено, дані замінено, після DELETE запис не існує |
| 4 | Фільтри та пагінація | `GET /records?category_id=1&status=done&limit=3&offset=0` | 200 | Фільтрація об'єднується через AND, пагінація детермінована, сортування за id |
| 5 | Валідація неприпустимих значень | `POST /records` (value=-1, title=" ", status="bad") | 422 | Відхилено валідатором Pydantic, запит до БД не відправляється |
| 6 | Перевірка числових меж | `POST /records` (value=11.0 > 10.0, value="str") | 422 | Заборонено перевищення діапазону [0.0; 10.0] та некоректні типи |
| 7 | Неіснуючі ресурси | `GET /records/99999`, `POST /records` (category_id=99999) | 404 | Повертається зрозуміле повідомлення про відсутність ресурсу |
| 8 | Конфлікт унікальності | `POST /records` (code="V13-01"), `POST /categories` ("iam") | 409 | Конфлікт відловлено, попередні записи залишаються незмінними |
| 9 | Цілісність зовнішнього ключа | `DELETE /categories/1` (непорожня) vs `DELETE /categories/4` (порожня) | 409 vs 204 | Блокування видалення непорожньої категорії (ON DELETE RESTRICT); порожня видаляється |
| 10 | Успішний пакетний запис (Bulk) | `POST /records/bulk` (2 нові записи) | 201 | Обидва записи додано в єдиній транзакції |
| 11 | Скасування пакета (дублікат коду) | `POST /records/bulk` (перший новий, другий code="V13-01") | 409 | Транзакцію відкочено (rollback); жоден запис пакета не зберігся |
| 12 | Скасування пакета (неіснуюча категорія)| `POST /records/bulk` (перший новий, другий category_id=99999) | 404 | Транзакцію скасовано, кількість записів у базі не змінилася |
| 13 | Перевірка захисту від SQL-ін'єкцій | `GET /records?q=' OR 1=1 --` | 200 | Рядок оброблено буквально як текст через `instr(title, ?)`, ін'єкцію нейтралізовано |
| 14 | Персистентність бази SQLite | `POST /records` -> перезапуск Uvicorn -> `GET /records/11` | 200 | Запис успішно зчитується з дискового файлу після повного перезапуску процесу |

### Результати перевірки Ruff
```powershell
PS C:\Users\vanay\OneDrive\Документи\GitHub\cybersecurity-python-labs> .\.venv\Scripts\ruff.exe check labs/lab03
All checks passed!
PS C:\Users\vanay\OneDrive\Документи\GitHub\cybersecurity-python-labs> .\.venv\Scripts\ruff.exe format --check labs/lab03
11 files already formatted
```

---

## Висновки
У ході виконання лабораторної роботи №3 було успішно опановано стек сучасних технологій для створення веб-застосунків та безпечних Web API мовою Python за допомогою фреймворку FastAPI та реляційної СКБД SQLite:
1. **Архітектурний розподіл відповідальності:** Реалізовано чітке розмежування рівнів системи: шар збереження даних (`database.py` та `repository.py`) працює автономно від веб-рівня, не імпортує FastAPI і транслює винятки бази даних у доменні помилки (`NotFoundError`, `ConflictError`). Маршрутизатори опрацьовують HTTP-запити, проводять перевірку параметрів і повертають строго типізовані моделі Pydantic.
2. **Параметризація та безпека:** Всі SQL-запити використовують параметризовані плейсхолдери `?`, повністю виключаючи можливість впровадження SQL-ін'єкцій. Для пошуку використано безпечну функцію `instr(title, ?)`, що запобігає маніпуляціям через шаблони `LIKE`.
3. **Цілісність даних:** Застосовано обмеження на рівні схеми SQLite (`NOT NULL`, `UNIQUE`, `CHECK`, `FOREIGN KEY ... ON DELETE RESTRICT`) та обов'язкову активацію `PRAGMA foreign_keys = ON;`.
4. **Атомарність транзакцій:** Реалізовано неподільне пакетне додавання знахідок (`POST /records/bulk`). Експериментально доведено, що при виникненні будь-якої помилки валідації або порушення унікальності відбувається автоматичний відкат транзакції (rollback), і база не переходить у частково оновлений стан.
5. **Якість коду:** Весь код лабораторної роботи повністю відповідає вимогам PEP 8 і без жодних зауважень пройшов перевірку статичного аналізатора та форматтера Ruff.

---

## Відповіді на контрольні питання

**1. Що означають таблиця, запис і поле? Які сутності описують ваші дві таблиці та який зв’язок між ними?**  
Таблиця — структурований набір даних, що моделює сутність предметної області. Поле (стовпець) визначає окрему характеристику сутності з фіксованим типом і обмеженнями. Запис (рядок) — конкретний екземпляр сутності. У роботі таблиця `categories` описує напрями аудиту хмарної безпеки (`iam`, `storage`, `network`), а `records` — знахідки ризиків конфігурації. Між ними реалізовано зв'язок «один до багатьох» (1:N): одна категорія містить багато знахідок через зовнішній ключ `category_id`.

**2. Чим відрізняються первинний і зовнішній ключі? Що станеться під час спроби створити запис із неіснуючою категорією?**  
Первинний ключ (`PRIMARY KEY`) однозначно ідентифікує запис у таблиці і не може бути `NULL`. Зовнішній ключ (`FOREIGN KEY`) посилається на первинний ключ іншої таблиці, забезпечуючи посилальну цілісність. При активній директиві `PRAGMA foreign_keys = ON` спроба створити запис із неіснуючою категорією викличе `sqlite3.IntegrityError`, який на рівні API повертає клієнту помилку `404 Not Found`.

**3. Чим файлова база SQLite відрізняється від CSV або JSON? Які можливості база додає для пошуку й підтримання узгодженості даних?**  
SQLite — це повноцінна реляційна СКБД, яка підтримує транзакції за стандартом ACID, індекси B-tree для швидкого пошуку, оптимізатор запитів, мову SQL і операції об'єднання `JOIN`. На відміну від плоских файлів, SQLite на рівні ядра гарантує збереження цілісності через обмеження `CHECK`, `UNIQUE` та `FOREIGN KEY`.

**4. Параметризовані запити: як вони захищають від SQL-ін’єкції? Чому ? не можна використати для довільної назви таблиці або поля?**  
Параметризований запит спочатку компілює структуру SQL-команди в байт-код, після чого підставляє значення на місця знаків `?` суворо як дані, що повністю унеможливлює зміну логіки запиту за допомогою спецсимволів лапок або коментарів. Знак `?` не можна використовувати для назв таблиць або полів, оскільки ці ідентифікатори необхідні парсеру для побудови плану виконання ще до передачі параметрів.

**5. Чому пакетне додавання потребує однієї транзакції? Що станеться, якщо виконувати commit() після кожного запису?**  
Пакетне додавання вимагає атомарності: зберегтися мають або всі записи пакета, або жоден. Якщо викликати `commit()` після кожного запису, то в разі помилки на n-му кроці попередні (n-1) записів уже зафіксуються в базі, що порушить узгодженість даних і залишить сміттєві записи.

**6. Що робить with connection у вашому коді? Чому після нього з’єднання все одно потрібно закрити?**  
Контекстний менеджер `with connection` керує транзакцією: автоматично викликає `commit()` при успішному завершенні блоку або `rollback()` у разі виникнення винятку. Проте він не закриває з'єднання з файлом БД. Незакрите з'єднання блокує ресурси ОС, тому його необхідно закривати через `with closing(get_connection()) as connection:`.

**7. Як співвідносяться GET, POST, PUT, DELETE з SQL-операціями? Чому в цій роботі PUT потребує всіх змінюваних полів?**  
`GET` відповідає `SELECT`, `POST` — `INSERT`, `PUT` — `UPDATE`, `DELETE` — `DELETE`. Метод `PUT` за стандартом HTTP є ідемпотентною операцією повної заміни стану ресурсу. Передача всіх змінюваних полів гарантує, що сутність не втратить пропущені поля і не перейде в частково ініціалізований стан.

**8. Чим відрізняються параметри шляху, параметри запиту та тіло запиту? Покажіть їх у власних маршрутах.**  
Параметр шляху ідентифікує конкретний ресурс у URI (`/records/{record_id}`). Параметр запиту уточнює критерії вибірки після знака `?` (`/records?category_id=1&status=done`). Тіло запиту передає структуровані JSON-дані для створення чи заміни об'єктів (`POST /records`, `POST /records/bulk`).

**9. Pydantic: що перевіряє модель запиту?**  
Модель (наприклад, `RecordCreate`) перевіряє типи даних, мінімальну й максимальну довжину рядків, обрізає крайні пробіли (`str_strip_whitespace=True`), перевіряє допустимі межі чисел (`ge=0.0`, `le=10.0`), забороняє нескінченності та `NaN` (`allow_inf_nan=False`), звіряє статус із фіксованим переліком `Literal` та блокує невідомі поля (`extra="forbid"`).

**10. Для чого потрібна response_model?**  
`response_model` гарантує, що клієнту повернуться лише явно описані поля (захист від витоку внутрішніх полів), перевіряє коректність вихідних даних на відповідність типам і генерує точну схему OpenAPI для документації Swagger UI.

**11. Чому модель створення не повинна приймати id запису?**  
Ідентифікатор `id` є сурогатним первинним ключем, генерацію якого контролює база даних. Якщо дозволити клієнту передавати `id`, це призведе до конфліктів унікальності, ризиків перезапису чужих записів (IDOR) та порушення інкапсуляції.

**12. HTTP-коди: наведіть приклади 201, 204, 404, 409 і 422 зі своєї роботи. Чому для 204 не повертають JSON-тіло?**  
- 201 Created: успішне додавання запису `POST /records`.
- 204 No Content: успішне видалення запису `DELETE /records/1` (тіло відсутнє, оскільки ресурс видалено і клієнту немає чого повертати).
- 404 Not Found: запис за `id` не знайдено або категорія не існує.
- 409 Conflict: дублікат унікального коду `code` або спроба видалити категорію з прив'язаними записами.
- 422 Unprocessable Entity: вхідні дані не пройшли валідацію Pydantic (наприклад, `value = -1` або `limit = 0`).

**13. Чому початковий JSON та код створення бази зберігаються в Git, а робочий файл SQLite — ні?**  
Файли коду (`schema.sql`, `seed.py`) та початкові дані (`seed.json`) є текстовими артефактами (Infrastructure as Code), які легко відстежувати у системі контролю версій і які дозволяють детерміновано відтворити базу на будь-якому комп'ютері. Файл `lab3.sqlite3` — це локальний бінарний стан, що спричиняє merge-конфлікти, роздуває розмір репозиторію та може містити неактуальні чи тестові сліди.
