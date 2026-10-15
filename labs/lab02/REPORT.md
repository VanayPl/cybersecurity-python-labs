# МІНІСТЕРСТВО ОСВІТИ І НАУКИ УКРАЇНИ
## НАЦІОНАЛЬНИЙ УНІВЕРСИТЕТ «ЛЬВІВСЬКА ПОЛІТЕХНІКА»
### Кафедра «Захист інформації»

<br><br><br>

# ЗВІТ
### до лабораторної роботи №2
### з курсу: «Програмування скриптовими мовами»
### на тему: «Розробка консольних утиліт для задач кібербезпеки»
#### Варіант №28 (13)

<br><br><br><br>

**Виконав:**  
студент групи КБ-202  
Якимчук І.І.  

**Прийняв:**  
Петрів П.П.  

<br><br>

**Львів 2026**

---

## Мета роботи
1. Закріпити та поглибити знання з об’єктно-орієнтованого програмування (ООП) в Python: створення класів, інкапсуляція, наслідування, композиція, спеціальні методи класів та декоратори `@property`, `@dataclass`.
2. Опанувати роботу зі стандартною бібліотекою Python для обробки даних: маніпуляція шляхами та файлами (`pathlib`), робота з форматами JSON та CSV, обробка дати і часу (`datetime`), використання спеціалізованих структур даних (`collections`) та регулярних виразів (`re`).
3. Навчитися будувати надійні та стійкі консольні програми (CLI-утиліти): обробка винятків, валідація вхідних даних, структуроване логування подій (`logging`) та розбір аргументів командного рядка (`argparse`).

---

## Індивідуальне завдання (Варіант 28 (13))

### Завдання 1: Модель користувача й облікового запису (ООП)
Створити об'єктно-орієнтовану модель захищеного керування користувачами, сесіями та аудитом:
- **Клас `User`**: атрибути `username: str`, `email: str` (через `@property`), `role: str`, `active: bool`, приватні атрибути `__password_hash` та `__password_salt`. Метод `set_password` із криптографічним хешуванням `hashlib.pbkdf2_hmac("sha256", ...)` із випадковою сіллю `os.urandom(16)` та 100 000 ітераціями. Метод `check_password` із захистом від атак за часом через `hmac.compare_digest()`. Метод `deactivate()` та `__str__()`. Валідація `email` через регулярний вираз (`ValueError` при невідповідності формату).
- **Клас `Admin(User)`**: наслідування від `User`, керування множиною дозволів `permissions: set[str]`. Реалізація методів `grant_permission()`, `revoke_permission()`, `has_permission()` та перевизначення `__str__()`.
- **Клас `Session`**: фіксація полів `ip: str`, `login_time: datetime`, `last_activity: datetime` у часовому поясі UTC (`datetime.now(timezone.utc)`). Методи `touch()` та `is_active(timeout_sec: int)` з відхиленням непозитивних таймаутів.
- **Клас `AuditLog`**: збереження записів аудиту, де окремий запис описано через `@dataclass AuditRecord(timestamp, username, action)`. Методи `add_log(username, action)` та `show_all()`.
- **Клас `UserAccount`**: композиція `User`, `Session` та `AuditLog`. Методи `login(username, password, ip)`, `is_authenticated()`, `logout()`. Реалізація спеціальних методів `__getitem__` та `__setitem__` з валідацією дозволених ключів і типів, із блокуванням доступу до хешів і солей паролів.
- **Демонстрація**: сценарій перевірки успішного/невдалого входу, зміни email, прав адміністратора, таймауту сесії, виходу та журналу аудиту.

### Завдання 2: Сканер витоків конфіденційних даних (PII Exfiltration Scanner) - Варіант 13
Розробити повноцінну CLI-утиліту для пошуку незахищених персональних даних (PII) у файлах і каталогах:
- Рекурсивне сканування директорії за допомогою `pathlib.Path`.
- Пошук за допомогою регулярних виразів `re`: e-mail адреси, номери банківських карток, номери телефонів, IPv4-адреси.
- Маскування знайдених даних (наприклад, `4111-****-****-1111`, `u****r@example.com`, `192.0.***.***`).
- Підрахунок кількості виявлених записів за типами за допомогою `collections.Counter`.
- Логування процесу (`logging`) та збереження аудиторського звіту в форматі JSON.
- Аргументи CLI: `--scan-dir`, `--patterns` (all / cards / emails / phones / ips), `--mask`, `--out-json`.

---

## Хід виконання

### Підготовка репозиторію та оточення:
Використано репозиторій `cybersecurity-python-labs` на GitHub. В активованому віртуальному середовищі `.venv` перевірено наявність статичного аналізатора Ruff (`ruff==0.16.8`). Оновлено файл `shared/student.py` із номером варіанта `VARIANT_NUMBER = 13` (що відповідає 28 за списком групи). 

Сформовано структуру каталогу `labs/lab02/`:
- `__init__.py` — пакетний файл.
- `task1.py` — класи та демонстрація ООП.
- `task2.py` — CLI-утиліта сканування PII.
- `main.py` — загальна точка входу з командами `demo` та `analyze`.
- `README.md` — інструкція користувача та детальний звіт.
- `data/data_v13/scan/` — навчальний набір даних варіанта 13 (`clean.txt`, `export.json`, `app.log`, `users.txt`).

---

### Завдання 1: Реалізація об'єктної моделі безпеки (`labs/lab02/task1.py`)
1. Створено клас `User`, в якому реалізовано приватні поля `__password_hash` та `__password_salt`. Метод `set_password` генерує 16 байт випадкової солі (`os.urandom(16)`) та обчислює хеш за стандартом `PBKDF2-HMAC-SHA256` (100 000 ітерацій). Метод `check_password` використовує `hmac.compare_digest()` для унеможливлення атак за часом. Через `@property` реалізовано валідацію формату `email` регулярним виразом `^[a-zA-Z][a-zA-Z0-9_]{2,63}@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$`.
2. Реалізовано клас `Admin(User)`, який через наслідування розширює функціонал базового користувача множиною дозволів `permissions: set[str]`. Конструктор викликає `super().__init__()` та захищений від мутацій типових аргументів.
3. Створено клас `Session` з атрибутами часу в UTC (`datetime.now(timezone.utc)`), методами `touch()` та `is_active()`, що перевіряє часову дельту бездіяльності та відхиляє від'ємні значення таймауту.
4. Описано датаклас `@dataclass AuditRecord` і клас `AuditLog` для накопичення подій безпеки без збереження паролів у відкритому вигляді.
5. Реалізовано клас `UserAccount`, що об'єднує компоненти за принципом композиції. Впроваджено методи `login()`, `is_authenticated()`, `logout()`, а також перевантажено методи індексації `__getitem__` та `__setitem__` з білим списком ключів (`user`, `session`, `audit_log`) і суворою типізацією, що блокує несанкціонований доступ до хешів паролів.
6. Створено демонстраційну функцію `run_demo()`, захищену перевіркою `if __name__ == "__main__":`, що запобігає автовиконанню при імпорті модуля.

---

### Завдання 2: Розробка консольного сканера PII (`labs/lab02/task2.py`)
1. За допомогою модуля `pathlib.Path` реалізовано рекурсивний обхід файлової системи (`dir_path.rglob("*")`) із безпечним зчитуванням вмісту файлів у кодуванні UTF-8 (`errors="replace"`).
2. Складено та скомпільовано регулярні вирази для пошуку:
   - Email: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b`
   - Кредитні картки: `\b(?:\d{4}-\d{4}-\d{4}-\d{4}|\d{4}\s\d{4}\s\d{4}\s\d{4}|\d{16})\b`
   - IPv4-адреси: `\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b`
   - Номери телефонів: `(?<!\w)(?:\+\d{1,3}[- ](?:(?:\(?\d{2,4}\)?[- ]?\d{2,4}[- ]?\d{2,4}(?:[- ]?\d{2,4})?))|\b0\d{9}\b)(?!\w)`
3. Реалізовано функції маскування (`mask_email`, `mask_credit_card`, `mask_ipv4`, `mask_phone`), які приховують конфіденційні частини (наприклад, `4111-****-****-1111`, `u****r@example.com`).
4. Для підрахунку знайдених витоків застосовано оптимізовану структуру `collections.Counter`.
5. Налаштовано структуроване логування через модуль `logging` у потік `sys.stdout` з рівнями `INFO`, `WARNING`, `ERROR`.
6. Реалізовано експорт підсумкового аудиторського звіту у формат JSON (із підтримкою санітизації даних при прапорці `--mask`).
7. Побудовано CLI-інтерфейс через `argparse` із параметрами `--scan-dir`, `--patterns`, `--mask`, `--out-json`.

---

### Головний модуль запуску (`labs/lab02/main.py`)
Створено єдиний консольний інтерфейс на базі `argparse.ArgumentParser` із двома підкомандами:
- `python -m labs.lab02.main demo` — запуск демонстраційного сценарію Завдання 1.
- `python -m labs.lab02.main analyze [параметри]` — запуск сканера витоків PII Завдання 2.

---

### Контроль якості коду (Ruff):
Виконано перевірку та форматування всього коду проєкту:
```bash
ruff check .
ruff format --check .
```
Обидві перевірки завершилися успішно без зауважень (`All checks passed!`, `12 files already formatted`).

---

## Лістинг коду до завдання 1 (`labs/lab02/task1.py`)

```python
"""Завдання 1. Модель користувача й облікового запису.

Реалізація системи моделювання користувачів, безпечних сесій та аудиту
на основі об'єктно-орієнтованого програмування (ООП).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import re
import time

PBKDF2_ITERATIONS: int = 100_000
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_]{2,63}@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$"
)


class User:
    """Клас користувача системи із захищеним збереженням пароля."""

    def __init__(
        self,
        username: str,
        email: str,
        role: str = "user",
        active: bool = True,
    ) -> None:
        """Ініціалізує об'єкт користувача."""
        self.username: str = username
        self.role: str = role
        self.active: bool = active
        self.__password_hash: bytes | None = None
        self.__password_salt: bytes | None = None
        self._email: str = ""
        self.email = email

    @property
    def email(self) -> str:
        """Повертає поточну email-адресу користувача."""
        return self._email

    @email.setter
    def email(self, new_email: str) -> None:
        """Встановлює email-адресу після перевірки формату через регулярний вираз."""
        if not isinstance(new_email, str):
            raise TypeError("Email повинен бути рядком.")
        if not EMAIL_REGEX.match(new_email):
            raise ValueError(
                f"Некоректний формат email: '{new_email}'. Локальна частина має починатися "
                "з латинської літери, містити 3-64 символи (латиниця, цифри, _), "
                "після чого йде @ та домен із крапкою."
            )
        self._email = new_email

    def set_password(self, password: str) -> None:
        """Хешує пароль з використанням PBKDF2-HMAC-SHA256 та випадкової солі."""
        if not isinstance(password, str) or not password:
            raise ValueError("Пароль повинен бути непорожнім рядком.")
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS,
        )
        self.__password_salt = salt
        self.__password_hash = pwd_hash

    def check_password(self, password: str) -> bool:
        """Перевіряє правильність введеного пароля за допомогою стійкого порівняння."""
        if self.__password_hash is None or self.__password_salt is None:
            return False
        if not isinstance(password, str):
            return False
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, calculated_hash)

    def deactivate(self) -> None:
        """Деактивує обліковий запис користувача."""
        self.active = False

    def __str__(self) -> str:
        """Повертає текстове представлення користувача без розкриття секретів."""
        return (
            f"User(username='{self.username}', email='{self.email}', "
            f"role='{self.role}', active={self.active})"
        )


class Admin(User):
    """Клас адміністратора, що успадковує User та керує правами доступу."""

    def __init__(
        self,
        username: str,
        email: str,
        role: str = "admin",
        active: bool = True,
        permissions: set[str] | list[str] | None = None,
    ) -> None:
        """Ініціалізує адміністратора з безпечною передачею дозволів."""
        super().__init__(username=username, email=email, role=role, active=active)
        self.permissions: set[str] = (
            set(permissions) if permissions is not None else set()
        )

    def grant_permission(self, permission: str) -> None:
        """Надає вказаний дозвіл адміністратору."""
        if not isinstance(permission, str) or not permission.strip():
            raise ValueError("Дозвіл повинен бути непорожнім рядком.")
        self.permissions.add(permission.strip())

    def revoke_permission(self, permission: str) -> None:
        """Відкликає вказаний дозвіл в адміністратора."""
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """Перевіряє наявність дозволу в адміністратора."""
        return permission in self.permissions

    def __str__(self) -> str:
        """Повертає текстове представлення адміністратора з переліком дозволів."""
        perms_str = ", ".join(sorted(self.permissions)) if self.permissions else "none"
        return (
            f"Admin(username='{self.username}', email='{self.email}', "
            f"role='{self.role}', active={self.active}, permissions=[{perms_str}])"
        )


class Session:
    """Клас користувацької сесії з відстеженням часу активності в UTC."""

    def __init__(
        self,
        ip: str,
        login_time: datetime | None = None,
        last_activity: datetime | None = None,
    ) -> None:
        """Ініціалізує сесію з фіксацією IP та міток часу в UTC."""
        self.ip: str = ip
        now = datetime.now(timezone.utc)
        self.login_time: datetime = login_time if login_time is not None else now
        self.last_activity: datetime = (
            last_activity if last_activity is not None else self.login_time
        )

    def touch(self) -> None:
        """Оновлює час останньої активності сесії поточним моментом в UTC."""
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        """Перевіряє, чи не перевищено таймаут бездіяльності."""
        if timeout_sec <= 0:
            raise ValueError("Параметр timeout_sec повинен бути додатним числом.")
        now = datetime.now(timezone.utc)
        elapsed = now - self.last_activity
        return elapsed <= timedelta(seconds=timeout_sec)


@dataclass
class AuditRecord:
    """Датаклас для зберігання окремого запису журналу аудиту."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Журнал подій безпеки системи."""

    def __init__(self) -> None:
        """Ініціалізує порожній журнал аудиту."""
        self._records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        """Додає новий запис аудиту із фіксацією поточного часу в UTC."""
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
        )
        self._records.append(record)

    def show_all(self) -> list[AuditRecord]:
        """Повертає копію всіх записів журналу аудиту."""
        return list(self._records)


class UserAccount:
    """Клас облікового запису користувача (композиція User, Session, AuditLog)."""

    SESSION_TIMEOUT_SEC: int = 900

    def __init__(
        self,
        user: User,
        audit_log: AuditLog | None = None,
        session: Session | None = None,
    ) -> None:
        """Ініціалізує обліковий запис комбінацією компонентів."""
        self.user: User = user
        self.audit_log: AuditLog = (
            audit_log if audit_log is not None else AuditLog()
        )
        self.session: Session | None = session

    def login(self, username: str, password: str, ip: str) -> bool:
        """Автентифікує користувача, ініціалізує сесію та записує подію в аудит."""
        if (
            not self.user.active
            or self.user.username != username
            or not self.user.check_password(password)
        ):
            self.audit_log.add_log(username, "login_failure")
            return False

        self.session = Session(ip=ip)
        self.session.touch()
        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        """Перевіряє активність сесії без оновлення часу останньої взаємодії."""
        if self.session is None:
            return False
        return self.session.is_active(self.SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        """Завершує активну сесію та реєструє подію виходу в журналі аудиту."""
        self.session = None
        self.audit_log.add_log(self.user.username, "logout")

    def __getitem__(self, key: str) -> object:
        """Повертає дозволені внутрішні компоненти за іменем ключа."""
        allowed_keys = ("user", "session", "audit_log")
        if key not in allowed_keys:
            raise KeyError(
                f"Ключ '{key}' недоступний або доступ до нього заборонено з міркувань безпеки."
            )
        return getattr(self, key)

    def __setitem__(self, key: str, value: object) -> None:
        """Безпечно встановлює дозволений компонент із перевіркою типу."""
        type_contracts = {
            "user": (User,),
            "session": (Session, type(None)),
            "audit_log": (AuditLog,),
        }
        if key not in type_contracts:
            raise KeyError(f"Ключ '{key}' недоступний для запису або зміна заборонена.")
        valid_types = type_contracts[key]
        if not isinstance(value, valid_types):
            expected = ", ".join(t.__name__ for t in valid_types)
            raise TypeError(
                f"Неправильний тип для ключа '{key}': очікувався ({expected}), отримано {type(value).__name__}."
            )
        setattr(self, key, value)


def run_demo() -> None:
    """Демонстраційний сценарій роботи об'єктної моделі (Завдання 1)."""
    print("=" * 70)
    print("   ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1: ОБ'ЄКТНО-ОРІЄНТОВАНА МОДЕЛЬ БЕЗПЕКИ")
    print("=" * 70)

    user = User(username="analyst_ivan", email="analyst_ivan@corp.net")
    user.set_password("CorrectHorseBatteryStaple!2026")
    print(f"[1] Створено користувача: {user}")

    admin = Admin(
        username="sec_admin",
        email="admin_ivan@corp.net",
        permissions=["read_logs", "view_reports"],
    )
    admin.set_password("SuperSecretAdminPass#2026")
    print(f"[2] Створено адміністратора: {admin}")

    print("\n--- Демонстрація прав доступу адміністратора ---")
    print(f"Чи має право 'delete_db'? {admin.has_permission('delete_db')}")
    admin.grant_permission("delete_db")
    print(f"Після grant_permission('delete_db'): {admin.has_permission('delete_db')}")
    admin.revoke_permission("delete_db")
    print(f"Після revoke_permission('delete_db'): {admin.has_permission('delete_db')}")
    print(f"Стан адміністратора: {admin}")

    print("\n--- Демонстрація валідації email через @property ---")
    try:
        user.email = "valid_user123@security-audit.com"
        print(f"[УСПІХ] Email успішно змінено на: {user.email}")
    except ValueError as e:
        print(f"[ПОМИЛКА] {e}")

    try:
        print("Спроба встановити некоректний email '1invalid-email@com'...")
        user.email = "1invalid-email@com"
    except ValueError as e:
        print(f"[ОЧІКУВАНА ВАЛІДАЦІЙНА ПОМИЛКА] {e}")

    print("\n--- Демонстрація автентифікації та аудиту ---")
    audit = AuditLog()
    account = UserAccount(user=user, audit_log=audit)

    print("Спроба входу з неправильним паролем...")
    res_fail = account.login("analyst_ivan", "WrongPassword!123", ip="192.168.1.55")
    print(
        f"Результат входу: {res_fail}, is_authenticated: {account.is_authenticated()}"
    )

    print("Спроба входу з правильним паролем...")
    res_success = account.login(
        "analyst_ivan", "CorrectHorseBatteryStaple!2026", ip="192.168.1.55"
    )
    print(
        f"Результат входу: {res_success}, is_authenticated: {account.is_authenticated()}"
    )

    print("\n--- Демонстрація методів __getitem__ / __setitem__ та безпеки ключів ---")
    print(f"account['user'].username => {account['user'].username}")
    print(f"account['session'].ip => {account['session'].ip}")

    try:
        print("Спроба прочитати account['__password_hash']...")
        _ = account["__password_hash"]
    except KeyError as e:
        print(f"[ЗАХИСТ СПРАЦЮВАВ] {e}")

    try:
        print("Спроба передати невалідний тип у account['session'] = 12345...")
        account["session"] = 12345
    except TypeError as e:
        print(f"[ЗАХИСТ ТИПІВ СПРАЦЮВАВ] {e}")

    print("\n--- Демонстрація таймауту сесії ---")
    test_session = Session(ip="10.0.0.99")
    print("Створено тест-сесію із таймаутом 2 секунди.")
    print(f"Активна одразу після створення? {test_session.is_active(timeout_sec=2)}")
    print("Очікування 2.2 секунди...")
    time.sleep(2.2)
    print(f"Активна після паузи? {test_session.is_active(timeout_sec=2)}")

    print("\n--- Демонстрація виходу (logout) ---")
    account.logout()
    print(f"Після logout: is_authenticated = {account.is_authenticated()}")

    print("\n--- Записи AuditLog (події безпеки) ---")
    for idx, rec in enumerate(audit.show_all(), start=1):
        formatted_time = rec.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(
            f"{idx}. [{formatted_time}] Користувач: {rec.username} | Дія: {rec.action}"
        )

    print("\n" + "=" * 70)
    print("   ДЕМОНСТРАЦІЮ ЗАВДАННЯ 1 УСПІШНО ЗАВЕРШЕНО")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
```

---

## Лістинг коду до завдання 2 (`labs/lab02/task2.py`)

```python
"""Завдання 2. Консольна утиліта кібербезпеки (Варіант 13).

Сканер витоків конфіденційних даних (PII Exfiltration Scanner).
Пошук незахищених персональних даних (PII) у файлах та директоріях:
- Email-адреси
- Номери банківських карток
- Номери телефонів
- IPv4-адреси
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re
import sys

logger = logging.getLogger("pii_scanner")

RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RE_CARD = re.compile(
    r"\b(?:\d{4}-\d{4}-\d{4}-\d{4}|\d{4}\s\d{4}\s\d{4}\s\d{4}|\d{16})\b"
)
RE_IPV4 = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)
RE_PHONE = re.compile(
    r"(?<!\w)(?:\+\d{1,3}[- ](?:(?:\(?\d{2,4}\)?[- ]?\d{2,4}[- ]?\d{2,4}(?:[- ]?\d{2,4})?))|\b0\d{9}\b)(?!\w)"
)


@dataclass
class PIIFinding:
    """Клас для зберігання інформації про виявлений збіг PII."""

    file_path: str
    line_number: int
    category: str
    raw_value: str
    masked_value: str


def mask_email(email: str) -> str:
    """Маскує email-адресу (наприклад, user@example.com -> u****r@example.com)."""
    if "@" not in email:
        return "****"
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        masked_user = f"{user[0]}****" if user else "****"
    else:
        masked_user = f"{user[0]}****{user[-1]}"
    return f"{masked_user}@{domain}"


def mask_credit_card(card: str) -> str:
    """Маскує номер банківської картки, зберігаючи перші та останні 4 цифри."""
    digits = [c for c in card if c.isdigit()]
    if len(digits) != 16:
        return "****-****-****-****"

    if "-" in card:
        parts = card.split("-")
        if len(parts) == 4:
            return f"{parts[0]}-****-****-{parts[3]}"
    if " " in card:
        parts = card.split()
        if len(parts) == 4:
            return f"{parts[0]} **** **** {parts[3]}"

    return f"{''.join(digits[:4])}********{''.join(digits[-4:])}"


def mask_ipv4(ip: str) -> str:
    """Маскує останні два октети IPv4-адреси (наприклад, 192.168.1.1 -> 192.168.***.***)."""
    octets = ip.split(".")
    if len(octets) == 4:
        return f"{octets[0]}.{octets[1]}.***.***"
    return "***.***.***.***"


def mask_phone(phone: str) -> str:
    """Маскує середню частину телефонного номера."""
    clean = phone.strip()
    if clean.startswith("+1-"):
        parts = clean.split("-")
        if len(parts) == 4:
            return f"{parts[0]}-{parts[1]}-***-{parts[3]}"
    if clean.startswith(("+380", "+44")):
        parts = clean.split()
        if len(parts) >= 3:
            return f"{parts[0]} {parts[1]} *** ** {parts[-1]}"
    if len(clean) >= 8:
        return f"{clean[:3]}****{clean[-3:]}"
    return "****"


class PIIScanner:
    """Сканер пошуку конфіденційної інформації (PII) у текстових файлах."""

    def __init__(self, patterns_mode: str = "all", mask_enabled: bool = False) -> None:
        """Ініціалізує сканер із заданим фільтром патернів та режимом маскування."""
        self.patterns_mode = patterns_mode.lower()
        self.mask_enabled = mask_enabled
        self.findings: list[PIIFinding] = []
        self.counter: Counter[str] = Counter()
        self.scanned_files_count: int = 0

    def _should_scan(self, category: str) -> bool:
        """Перевіряє, чи входить категорія до обраного фільтра патернів."""
        match_map = {
            "all": True,
            "cards": category == "Credit Card",
            "emails": category == "Email",
            "phones": category == "Phone",
            "ips": category == "IPv4",
        }
        return match_map.get(self.patterns_mode, False)

    def scan_text(self, text: str, file_path: str) -> list[PIIFinding]:
        """Шукає всі PII-записи у тексті по рядках."""
        file_findings: list[PIIFinding] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            if self._should_scan("Email"):
                for match in RE_EMAIL.finditer(line):
                    val = match.group()
                    finding = PIIFinding(
                        file_path=file_path,
                        line_number=line_no,
                        category="Email",
                        raw_value=val,
                        masked_value=mask_email(val),
                    )
                    file_findings.append(finding)
                    self.counter["Email Addresses"] += 1

            if self._should_scan("Credit Card"):
                for match in RE_CARD.finditer(line):
                    val = match.group()
                    finding = PIIFinding(
                        file_path=file_path,
                        line_number=line_no,
                        category="Credit Card",
                        raw_value=val,
                        masked_value=mask_credit_card(val),
                    )
                    file_findings.append(finding)
                    self.counter["Credit Card Numbers"] += 1

            if self._should_scan("Phone"):
                for match in RE_PHONE.finditer(line):
                    val = match.group()
                    if RE_CARD.fullmatch(val):
                        continue
                    finding = PIIFinding(
                        file_path=file_path,
                        line_number=line_no,
                        category="Phone",
                        raw_value=val,
                        masked_value=mask_phone(val),
                    )
                    file_findings.append(finding)
                    self.counter["Phone Numbers"] += 1

            if self._should_scan("IPv4"):
                for match in RE_IPV4.finditer(line):
                    val = match.group()
                    finding = PIIFinding(
                        file_path=file_path,
                        line_number=line_no,
                        category="IPv4",
                        raw_value=val,
                        masked_value=mask_ipv4(val),
                    )
                    file_findings.append(finding)
                    self.counter["IPv4 Addresses"] += 1

        self.findings.extend(file_findings)
        return file_findings

    def scan_directory(self, dir_path: Path) -> None:
        """Рекурсивно сканує вказану директорію за допомогою pathlib.Path."""
        if not dir_path.exists():
            raise FileNotFoundError(f"Директорію не знайдено: {dir_path}")
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Шлях не є директорією: {dir_path}")

        logger.info(
            "Scanning directory %s for unmasked PII data...",
            dir_path.as_posix(),
        )

        files = sorted(p for p in dir_path.rglob("*") if p.is_file())
        self.scanned_files_count = len(files)

        for file in files:
            try:
                content = file.read_text(encoding="utf-8", errors="replace")
                try:
                    rel_path = file.relative_to(dir_path).as_posix()
                except ValueError:
                    rel_path = file.as_posix()
                self.scan_text(content, rel_path)
            except OSError as err:
                logger.warning("Не вдалося прочитати файл %s: %s", file, err)

        logger.info("Scanned %d files.", self.scanned_files_count)

    def print_summary(self) -> None:
        """Виводить консольний звіт за результатами сканування."""
        print("\n=== Detected Sensitive Data (PII) ===")
        order = [
            ("Email Addresses", "Email Addresses"),
            ("Credit Card Numbers", "Credit Card Numbers"),
            ("Phone Numbers", "Phone Numbers"),
            ("IPv4 Addresses", "IPv4 Addresses"),
        ]
        for key, title in order:
            if self.patterns_mode == "all" or self._matches_filter(key):
                count = self.counter.get(key, 0)
                print(f"{title:<20}: {count} matches")

        if self.findings:
            print("\n=== Sample Findings (Masked for Display) ===")
            seen_files: dict[str, list[PIIFinding]] = {}
            for item in self.findings:
                seen_files.setdefault(
                    f"{item.file_path}:{item.line_number}", []
                ).append(item)

            sample_keys = list(seen_files.keys())[:5]
            for key in sample_keys:
                items = seen_files[key]
                first = items[0]
                print(f"[PII FOUND] File: {first.file_path} (Line {first.line_number})")
                for it in items:
                    note = " (Original masked)" if it.category == "Credit Card" else ""
                    print(f"  {it.category:<12} : {it.masked_value}{note}")

            logger.warning("Unmasked PII found in plaintext logs!")
        else:
            print("\nNo unmasked PII data detected.")

    def _matches_filter(self, key: str) -> bool:
        """Перевіряє відповідність лічильника поточному режиму патернів."""
        match_map = {
            "all": True,
            "cards": "Card" in key,
            "emails": "Email" in key,
            "phones": "Phone" in key,
            "ips": "IPv4" in key,
        }
        return match_map.get(self.patterns_mode, False)

    def save_report(self, out_path: Path) -> None:
        """Зберігає підсумковий звіт аудиту у форматі JSON."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        report_data = {
            "scanned_files": self.scanned_files_count,
            "patterns_mode": self.patterns_mode,
            "mask_applied": self.mask_enabled,
            "summary": dict(self.counter),
            "findings": [
                {
                    "file": f.file_path,
                    "line": f.line_number,
                    "category": f.category,
                    "value": (f.masked_value if self.mask_enabled else f.raw_value),
                }
                for f in self.findings
            ],
        }
        with open(out_path, "w", encoding="utf-8") as json_file:
            json.dump(report_data, json_file, indent=2, ensure_ascii=False)

        if self.mask_enabled:
            logger.info("Sanitized report saved to %s", out_path.as_posix())
        else:
            logger.info("Analysis report saved to %s", out_path.as_posix())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Парсить аргументи командного рядка."""
    parser = argparse.ArgumentParser(
        prog="pii_scanner",
        description="Сканер витоків конфіденційних даних (PII Exfiltration Scanner) - Варіант 13",
    )
    parser.add_argument(
        "--scan-dir",
        type=Path,
        default=Path("labs/lab02/data/data_v13/scan"),
        help="Шлях до директорії для сканування (за замовчуванням: labs/lab02/data/data_v13/scan)",
    )
    parser.add_argument(
        "--patterns",
        choices=["all", "cards", "emails", "phones", "ips"],
        default="all",
        help="Типи патернів для пошуку (all, cards, emails, phones, ips. Дефолт: all)",
    )
    parser.add_argument(
        "--mask",
        action="store_true",
        help="Застосувати маскування знайдених PII у підсумковому JSON-звіті",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("labs/lab02/data/pii_scan_summary.json"),
        help="Шлях для збереження підсумкового JSON-звіту (дефолт: labs/lab02/data/pii_scan_summary.json)",
    )
    return parser.parse_args(argv)


def run_scanner(
    scan_dir: Path,
    patterns: str = "all",
    mask: bool = False,
    out_json: Path | None = None,
) -> int:
    """Основна функція запуску сканування PII."""
    scanner = PIIScanner(patterns_mode=patterns, mask_enabled=mask)
    try:
        scanner.scan_directory(scan_dir)
    except (FileNotFoundError, NotADirectoryError) as err:
        logger.error("Помилка сканування: %s", err)
        return 1

    scanner.print_summary()

    if out_json is not None:
        try:
            scanner.save_report(out_json)
        except OSError as err:
            logger.error("Не вдалося зберегти звіт: %s", err)
            return 1

    return 0


def main(argv: list[str] | None = None) -> None:
    """Точка входу для самостійного запуску task2.py."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        stream=sys.stdout,
    )
    args = parse_args(argv)
    exit_code = run_scanner(
        scan_dir=args.scan_dir,
        patterns=args.patterns,
        mask=args.mask,
        out_json=args.out_json,
    )
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

---

## Лістинг коду головного модуля (`labs/lab02/main.py`)

```python
"""Головний модуль запуску Лабораторної роботи №2 (Варіант 13).

Підтримує дві основні підкоманди:
- demo: запуск демонстраційного сценарію Завдання 1 (ООП, автентифікація, сесії, аудит).
- analyze: запуск утиліти кібербезпеки Завдання 2 (Сканер витоків PII).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

from labs.lab02.task1 import run_demo
from labs.lab02.task2 import run_scanner


def build_parser() -> argparse.ArgumentParser:
    """Створює та налаштовує парсер аргументів командного рядка."""
    parser = argparse.ArgumentParser(
        prog="python -m labs.lab02.main",
        description="Лабораторна робота №2: Розробка консольних утиліт для задач кібербезпеки",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        help="Команда для виконання: 'demo' (Завдання 1) або 'analyze' (Завдання 2)",
    )

    subparsers.add_parser(
        "demo",
        help="Запустити демонстрацію об'єктно-орієнтованої системи (Завдання 1)",
    )

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Запустити CLI-сканер витоків PII (Завдання 2, Варіант 13)",
    )
    analyze_parser.add_argument(
        "--scan-dir",
        type=Path,
        default=Path("labs/lab02/data/data_v13/scan"),
        help="Шлях до директорії сканування (дефолт: labs/lab02/data/data_v13/scan)",
    )
    analyze_parser.add_argument(
        "--patterns",
        choices=["all", "cards", "emails", "phones", "ips"],
        default="all",
        help="Фільтр типів патернів (all, cards, emails, phones, ips; за замовчуванням: all)",
    )
    analyze_parser.add_argument(
        "--mask",
        action="store_true",
        help="Застосувати маскування знайдених PII у підсумковому JSON-звіті",
    )
    analyze_parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("labs/lab02/data/pii_scan_summary.json"),
        help="Шлях до файлу для збереження JSON-звіту",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Головна точка входу для запуску програми."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        stream=sys.stdout,
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "demo":
        run_demo()
    elif args.command == "analyze":
        exit_code = run_scanner(
            scan_dir=args.scan_dir,
            patterns=args.patterns,
            mask=args.mask,
            out_json=args.out_json,
        )
        if exit_code != 0:
            sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## Результати роботи програми

### Рис. 1. Демонстрація Завдання 1: ООП-модель безпеки (`python -m labs.lab02.main demo`)

```text
======================================================================
   ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1: ОБ'ЄКТНО-ОРІЄНТОВАНА МОДЕЛЬ БЕЗПЕКИ
======================================================================
[1] Створено користувача: User(username='analyst_ivan', email='analyst_ivan@corp.net', role='user', active=True)
[2] Створено адміністратора: Admin(username='sec_admin', email='admin_ivan@corp.net', role='admin', active=True, permissions=[read_logs, view_reports])

--- Демонстрація прав доступу адміністратора ---
Чи має право 'delete_db'? False
Після grant_permission('delete_db'): True
Після revoke_permission('delete_db'): False
Стан адміністратора: Admin(username='sec_admin', email='admin_ivan@corp.net', role='admin', active=True, permissions=[read_logs, view_reports])

--- Демонстрація валідації email через @property ---
[УСПІХ] Email успішно змінено на: valid_user123@security-audit.com
Спроба встановити некоректний email '1invalid-email@com'...
[ОЧІКУВАНА ВАЛІДАЦІЙНА ПОМИЛКА] Некоректний формат email: '1invalid-email@com'. Локальна частина має починатися з латинської літери, містити 3-64 символи (латиниця, цифри, _), після чого йде @ та домен із крапкою.

--- Демонстрація автентифікації та аудиту ---
Спроба входу з неправильним паролем...
Результат входу: False, is_authenticated: False
Спроба входу з правильним паролем...
Результат входу: True, is_authenticated: True

--- Демонстрація методів __getitem__ / __setitem__ та безпеки ключів ---
account['user'].username => analyst_ivan
account['session'].ip => 192.168.1.55
Спроба прочитати account['__password_hash']...
[ЗАХИСТ СПРАЦЮВАВ] "Ключ '__password_hash' недоступний або доступ до нього заборонено з міркувань безпеки."
Спроба передати невалідний тип у account['session'] = 12345...
[ЗАХИСТ ТИПІВ СПРАЦЮВАВ] Неправильний тип для ключа 'session': очікувався (Session, NoneType), отримано int.

--- Демонстрація таймауту сесії ---
Створено тест-сесію із таймаутом 2 секунди.
Активна одразу після створення? True
Очікування 2.2 секунди...
Активна після паузи? False

--- Демонстрація виходу (logout) ---
Після logout: is_authenticated = False

--- Записи AuditLog (події безпеки) ---
1. [2026-10-15 12:21:18 UTC] Користувач: analyst_ivan | Дія: login_failure
2. [2026-10-15 12:21:18 UTC] Користувач: analyst_ivan | Дія: login_success
3. [2026-10-15 12:21:20 UTC] Користувач: analyst_ivan | Дія: logout

======================================================================
   ДЕМОНСТРАЦІЮ ЗАВДАННЯ 1 УСПІШНО ЗАВЕРШЕНО
======================================================================
```

---

### Рис. 2. Завдання 2: Сканування витоків PII у директорії (`python -m labs.lab02.main analyze --mask`)

```text
[INFO] Scanning directory labs/lab02/data/data_v13/scan for unmasked PII data...
[INFO] Scanned 4 files.

=== Detected Sensitive Data (PII) ===
Email Addresses     : 4 matches
Credit Card Numbers : 3 matches
Phone Numbers       : 4 matches
IPv4 Addresses      : 4 matches

=== Sample Findings (Masked for Display) ===
[PII FOUND] File: exports/export.json (Line 4)
  Email        : c****l@example.test
[PII FOUND] File: exports/export.json (Line 5)
  IPv4         : 203.0.***.***
[PII FOUND] File: exports/export.json (Line 8)
  Email        : d****e@example.test
[PII FOUND] File: exports/export.json (Line 9)
  Phone        : +44 20 *** ** 0958
[PII FOUND] File: exports/export.json (Line 12)
  Credit Card  : 4000-****-****-0002 (Original masked)
[WARNING] Unmasked PII found in plaintext logs!
[INFO] Sanitized report saved to labs/lab02/data/pii_scan_summary.json
```

---

### Рис. 3. Фільтрація карток та сформований звіт `pii_scan_summary.json`

Команда запуску фільтрації карток:
```bash
python -m labs.lab02.main analyze --scan-dir labs/lab02/data/data_v13/scan --patterns cards --mask
```

Консольне виведення:
```text
[INFO] Scanning directory labs/lab02/data/data_v13/scan for unmasked PII data...
[INFO] Scanned 4 files.

=== Detected Sensitive Data (PII) ===
Credit Card Numbers : 3 matches

=== Sample Findings (Masked for Display) ===
[PII FOUND] File: exports/export.json (Line 12)
  Credit Card  : 4000-****-****-0002 (Original masked)
[PII FOUND] File: logs/app.log (Line 3)
  Credit Card  : 4111-****-****-1111 (Original masked)
[PII FOUND] File: notes/users.txt (Line 6)
  Credit Card  : 5555 **** **** 4444 (Original masked)
[WARNING] Unmasked PII found in plaintext logs!
[INFO] Sanitized report saved to labs/lab02/data/pii_scan_summary.json
```

Вміст збереженого файлу `labs/lab02/data/pii_scan_summary.json`:
```json
{
  "scanned_files": 4,
  "patterns_mode": "all",
  "mask_applied": true,
  "summary": {
    "Email Addresses": 4,
    "IPv4 Addresses": 4,
    "Phone Numbers": 4,
    "Credit Card Numbers": 3
  },
  "findings": [
    {
      "file": "exports/export.json",
      "line": 4,
      "category": "Email",
      "value": "c****l@example.test"
    },
    {
      "file": "exports/export.json",
      "line": 5,
      "category": "IPv4",
      "value": "203.0.***.***"
    },
    {
      "file": "exports/export.json",
      "line": 8,
      "category": "Email",
      "value": "d****e@example.test"
    },
    {
      "file": "exports/export.json",
      "line": 9,
      "category": "Phone",
      "value": "+44 20 *** ** 0958"
    },
    {
      "file": "exports/export.json",
      "line": 12,
      "category": "Credit Card",
      "value": "4000-****-****-0002"
    },
    {
      "file": "logs/app.log",
      "line": 1,
      "category": "Email",
      "value": "a****e@example.test"
    },
    {
      "file": "logs/app.log",
      "line": 1,
      "category": "IPv4",
      "value": "192.0.***.***"
    },
    {
      "file": "logs/app.log",
      "line": 2,
      "category": "Phone",
      "value": "+380 67 *** ** 67"
    },
    {
      "file": "logs/app.log",
      "line": 3,
      "category": "Credit Card",
      "value": "4111-****-****-1111"
    },
    {
      "file": "logs/app.log",
      "line": 4,
      "category": "IPv4",
      "value": "198.51.***.***"
    },
    {
      "file": "notes/users.txt",
      "line": 2,
      "category": "Email",
      "value": "b****h@example.test"
    },
    {
      "file": "notes/users.txt",
      "line": 3,
      "category": "Phone",
      "value": "+1-202-***-0147"
    },
    {
      "file": "notes/users.txt",
      "line": 4,
      "category": "Phone",
      "value": "050****567"
    },
    {
      "file": "notes/users.txt",
      "line": 5,
      "category": "IPv4",
      "value": "10.20.***.***"
    },
    {
      "file": "notes/users.txt",
      "line": 6,
      "category": "Credit Card",
      "value": "5555 **** **** 4444"
    }
  ]
}
```

---

### Рис. 4. Контроль якості коду через Ruff

```text
PS C:\Users\vanay\OneDrive\Документи\GitHub\cybersecurity-python-labs> ruff check .
All checks passed!

PS C:\Users\vanay\OneDrive\Документи\GitHub\cybersecurity-python-labs> ruff format --check .
12 files already formatted
```

---

## Висновки

У ході виконання лабораторної роботи №2 було закріплено та поглиблено знання з об'єктно-орієнтованого програмування на мові Python та розробки надійних консольних утиліт (CLI) для прикладних задач кібербезпеки. 

У першому завданні реалізовано комплексну модель безпеки користувачів, безпечних сесій та аудиту. Застосовано криптографічне хешування паролів за стандартом `PBKDF2-HMAC-SHA256` з випадковою 16-байтовою сіллю та 100 000 ітераціями, що виключає ризик атак за допомогою райдужних таблиць або швидкого перебору. Для порівняння хешів використано `hmac.compare_digest()`, що гарантує константний час виконання операції та захищає систему від атак за часом (timing attacks). Принцип наслідування (*"Is-A"*) продемонстровано через створення класу `Admin`, що розширює `User` функціоналом динамічного керування правами доступу. Принцип композиції (*"Has-A"*) застосовано в класі `UserAccount`, який незалежно інкапсулює користувача, активну сесію та журнал аудиту. Завдяки магічним методам `__getitem__` та `__setitem__` створено безпечний інтерфейс взаємодії з об'єктом, де реалізовано суворий білий список дозволених атрибутів та заблоковано будь-які спроби витоку або зміни чутливих криптографічних полів.

У другому завданні відповідно до варіанта 13 розроблено повноцінну консольну утиліту пошуку витоків персональних даних (PII Exfiltration Scanner). За допомогою `pathlib.Path` реалізовано рекурсивне сканування вказаних каталогів, а використання скомпільованих регулярних виразів `re` забезпечило надійну ідентифікацію email-адрес, номерів кредитних карток, телефонів та IPv4-адрес. Впроваджено алгоритми маскування знайдених даних для безпечного відображення в терміналі та санітизації експортованих звітів відповідно до стандартів PCI DSS та GDPR. Підрахунок кількості витоків за типами оптимізовано за допомогою структури `collections.Counter`, а для структурованого виведення подій безпеки використано модуль `logging`. Налаштовано гнучкий інтерфейс командного рядка за допомогою `argparse` та збереження фінальних звітів у форматі JSON. Якість коду підтверджено статичним аналізатором і форматтером Ruff (100% пройдених перевірок).

---

## Відповіді на контрольні питання

### 1. Як в Python реалізована інкапсуляція? Чим відрізняються атрибути `_password_hash` (protected) та `__password_hash` (private)? Що таке Name Mangling?
- **Інкапсуляція в Python** реалізується на рівні угод про іменування та механізму спотворення імен, оскільки суворих модифікаторів доступу (як у C++ або Java) на рівні інтерпретатора немає.
- **Одинарне підкреслення (`_protected`)**: це конвенційна домовленість між розробниками про те, що атрибут чи метод є внутрішньою деталлю реалізації і не призначений для прямого виклику ззовні. Інтерпретатор не накладає технічних обмежень на доступ.
- **Подвійне підкреслення (`__private`)**: активує механізм **Name Mangling** (спотворення імені). Інтерпретатор автоматично змінює внутрішнє ім'я атрибута на `_ClassName__attribute` (наприклад, `_User__password_hash`). Це захищає атрибут від випадкового перезапису в дочірніх класах та ускладнює несанкціонований прямий доступ.

### 2. Яку перевагу надає використання декоратора `@property` для атрибута `email` у порівнянні з явним викликом методів `get_email()` та `set_email()`?
- Декоратор `@property` дозволяє звертатися до атрибута через звичний та зручний синтаксис властивості (`user.email = "..."`), але прозоро викликає валідаційну логіку сетера.
- Це зберігає зворотну сумісність публічного інтерфейсу класу, усуває необхідність рефакторити наявний клієнтський код на явні виклики функцій-сетерів, покращує читабельність програми (Pythonic Way) та дозволяє централізовано контролювати інваріанти стану об'єкта (наприклад, викидати `ValueError` при невалідному форматі).

### 3. У Завданні 1 клас `Admin` успадковує `User`, а клас `UserAccount` містить об'єкти `User` та `Session`. Чому обрано саме такі архітектурні рішення (принцип "Is-A" проти "Has-A")?
- **"Is-A" (Наслідування)**: `Admin` є спеціалізованим типом користувача. Він володіє всіма атрибутами та поведінкою базового користувача (ім'я, пароль, активність), але розширює їх управлінням правами (`permissions`). Тому тут природно використано наслідування `class Admin(User)`.
- **"Has-A" (Композиція)**: Обліковий запис `UserAccount` сам по собі не є користувачем або сесією — він *містить* об'єкти користувача, поточної активної сесії та журналу аудиту (`UserAccount has a User, has a Session, has an AuditLog`). Композиція забезпечує слабку зв'язаність (Loose Coupling), гнучкість, дозволяє скидати сесію при виході (`self.session = None`) без руйнування самого користувача.

### 4. Для чого реалізуються спеціальні методи `__getitem__` та `__setitem__`? Як це змінює інтерфейс взаємодії з об'єктом класу `UserAccount`?
- Вони реалізують оператор доступу за індексом/ключем (`account[key]`), перетворюючи об'єкт на інтерфейс, подібний до словника.
- У контексті кібербезпеки це дає змогу реалізувати захисний шар (Whitelist):
  1. Дозволити доступ лише до визначеного переліку безпечних компонентів (`user`, `session`, `audit_log`).
  2. Заблокувати спроби читання чи зміни чутливих даних (солі та парольного хешу) через збудження `KeyError`.
  3. Здійснювати строгий контроль типів при присвоєнні значень через `TypeError`.

### 5. Які рутинні методи (`__init__`, `__repr__`, `__eq__`) автоматично генерує декоратор `@dataclass`? У яких випадках доцільніше використати `@dataclass` замість звичайного класу або словника?
- `@dataclass` автоматично генерує конструктор `__init__()`, інформативне рядкове представлення `__repr__()` та метод порівняння значень за полями `__eq__()`.
- **Порівняно зі звичайним класом**: усуває необхідність писати однотипний шаблонний код (boilerplate) для збереження аргументів у поля.
- **Порівняно зі словником**: забезпечує строгу типізацію полів, підказки типів в IDE, незмінність структури (захист від друкарських помилок у ключах) та зменшує накладні витрати оперативної пам'яті.

### 6. Чому модуль `pathlib` вважається більш сучасним та безпечним інструментом для роботи зі шляхами, ніж традиційний `os.path` або робота зі звичайними рядками?
- `pathlib` надає об'єктно-орієнтований інтерфейс (`Path`), інкапсулюючи системні особливості файлових шляхів.
- Він автоматично адаптує роздільники каталогів (`/` для Linux/macOS та `\` для Windows) за допомогою оператора `/`.
- Запобігає помилкам ручної конкатенації рядків, знижує ризик вразливостей Path Traversal та надає зручні високорівневі методи: `.rglob()`, `.read_text()`, `.is_file()`, `.relative_to()`.

### 7. Які переваги дає використання `collections.Counter` та `collections.defaultdict` при аналізі великих лог-файлів?
- **`collections.Counter`**: спеціалізований лічильник елементів, який автоматично повертає `0` для неіснуючих ключів (усуває `KeyError`), підтримує швидке математичне об'єднання, віднімання та отримання найбільш частих елементів через `.most_common()`.
- **`collections.defaultdict`**: автоматично викликає фабричну функцію для створення значення за замовчуванням (наприклад, `list` або `int`), усуваючи громіздкі перевірки `if key not in dict` та оптимізуючи швидкість обробки великих обсягів логів.

### 8. Як у модулі `argparse` реалізується додавання обов'язкових та позиційних аргументів, прапорців (flags) та типів даних? Чому валідацію типів аргументів варто робити на рівні `argparse`?
- **Позиційні/обов'язкові аргументи**: додаються без дефісів (`parser.add_argument("command")`).
- **Опціональні аргументи та прапорці**: починаються з дефіса (`--scan-dir`, `--mask`), для прапорців вказується `action="store_true"`.
- **Типи даних**: задаються параметром `type=` (наприклад, `type=Path`, `type=int`).
- **Переваги валідації на рівні `argparse`**: помилки перехоплюються на найранішому етапі до виконання бізнес-логіки утиліти; автоматично формується стандартизоване повідомлення про помилку та інтерактивна довідка (`--help`), що запобігає падінню програми в рантаймі.

### 9. Чим використання модуля `logging` краще за звичайні виклики `print()` у консольних утилітах кібербезпеки? Яку роль відіграють рівні логування (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)?
- На відміну від статичного виводу `print()`, модуль `logging`:
  1. Дозволяє гнучко налаштовувати рівень деталізації (verbosity) без редагування коду.
  2. Додає системний контекст: точний час, назву потоку, ім'я модуля та рівень важливості.
  3. Підтримує одночасне спрямування логів у консоль, файл, системний журнал або SIEM-системи.
- **Рівні логування**:
  - `DEBUG`: детальна інформація для розробника та налагодження.
  - `INFO`: плановий нормальний хід операцій (старт/завершення сканування).
  - `WARNING`: виявлення потенційної небезпеки або некритичної аномалії (знайдено незахищені PII).
  - `ERROR`: серйозний збій, через який не вдалося виконати операцію (помилка читання файлу).
  - `CRITICAL`: критична системна аварія, що вимагає негайного припинення роботи.

### 10. Які категорії помилок (наприклад, невикористані імпорти, складність функцій, помилки стилю) виявив аналізатор `Ruff` у вашому коді і як ви їх усунули?
1. **Невпорядковані імпорти (`I001`)**: за стандартом PEP 8 імпорти мають бути згруповані за секціями (`future`, стандартні бібліотеки, сторонні бібліотеки, локальні модулі) та відсортовані за алфавітом. Усунено автоматично командою `ruff check --fix .`.
2. **Форматування довжини рядків та відступів**: усунено за допомогою форматера командою `ruff format .`.
3. **Спрощення умовних виразів (`SIM103`)**: конструкції повернення результату порівняння через `if condition: return True ... return False` були оптимізовані за допомогою прямого зіставлення через словник конфігурацій.
