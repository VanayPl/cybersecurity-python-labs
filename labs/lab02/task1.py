"""Завдання 1. Модель користувача й облікового запису.

Реалізація системи моделювання користувачів, безпечних сесій та аудиту
на основі об'єктно-орієнтованого програмування (ООП).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

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
        self.email = email  # Виклик @email.setter для валідації

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
        self.audit_log: AuditLog = audit_log if audit_log is not None else AuditLog()
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

    # 1. Створення звичайного користувача та адміністратора
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

    # Демонстрація прав адміністратора
    print("\n--- Демонстрація прав доступу адміністратора ---")
    print(f"Чи має право 'delete_db'? {admin.has_permission('delete_db')}")
    admin.grant_permission("delete_db")
    print(f"Після grant_permission('delete_db'): {admin.has_permission('delete_db')}")
    admin.revoke_permission("delete_db")
    print(f"Після revoke_permission('delete_db'): {admin.has_permission('delete_db')}")
    print(f"Стан адміністратора: {admin}")

    # 2. Валідація email через @property
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

    # 3. Обліковий запис, автентифікація та аудит
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

    # 4. Спеціальні методи __getitem__ та __setitem__ і захист хешу
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
        account["session"] = 12345  # type: ignore[assignment]
    except TypeError as e:
        print(f"[ЗАХИСТ ТИПІВ СПРАЦЮВАВ] {e}")

    # 5. Демонстрація завершення сесії за таймаутом
    print("\n--- Демонстрація таймауту сесії ---")
    test_session = Session(ip="10.0.0.99")
    print("Створено тест-сесію із таймаутом 2 секунди.")
    print(f"Активна одразу після створення? {test_session.is_active(timeout_sec=2)}")
    print("Очікування 2.2 секунди...")
    time.sleep(2.2)
    print(f"Активна після паузи? {test_session.is_active(timeout_sec=2)}")

    # 6. Вихід з облікового запису
    print("\n--- Демонстрація виходу (logout) ---")
    account.logout()
    print(f"Після logout: is_authenticated = {account.is_authenticated()}")

    # 7. Перегляд журналів аудиту
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
