import csv
import datetime
import functools
import hashlib
import json
import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from shared.student import VARIANT_NUMBER

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "data")
)
USERS_CSV = os.path.join(DATA_DIR, "users.csv")
LOG_JSON = os.path.join(DATA_DIR, "log.json")

MIN_PASSWORD_LENGTH = 14
SALT = str(VARIANT_NUMBER).zfill(5)

users_to_register = (
    ("admin_usr", "AdminStrongP@ss14"),
    ("analyst_1", "SecretPass#2026!"),
    ("dev_ops_2", "DeploySecure@Cloud1"),
    ("researcher", "ValidP@ssword123"),
    ("engineer_4", "ProtectData#9999"),
    ("intern_usr", "InternWelcome@2026"),
    ("sec_audit", "AuditMasterKey!7"),
    ("qa_tester", "QualityAssurance#1"),
    ("cloud_user", "MyBigCloudPass@8"),
    ("guest_acc", "TemporaryGuest#10"),
)


class ValidationError(Exception):
    pass


def generate_hash(password: str, salt: str = "00000") -> str:
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Довжина пароля має бути не менше {MIN_PASSWORD_LENGTH} символів"
        )
    salted = password + salt
    return hashlib.sha3_256(salted.encode("utf-8")).hexdigest()


def create_user(username: str, password: str) -> tuple:
    hash_val = generate_hash(password, SALT)
    return (username, hash_val)


def create_users(users_list):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password_hash"])
            for u, p in users_list:
                user_record = create_user(u, p)
                writer.writerow(user_record)
    except (FileNotFoundError, PermissionError, IOError) as e:
        print(f"Помилка створення файлу бази даних: {e}")


def read_users_db():
    users_db = []
    try:
        with open(USERS_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if row:
                    users_db.append(tuple(row))
    except (FileNotFoundError, PermissionError, IOError) as e:
        print(f"Помилка читання бази даних: {e}")
    return users_db


def log_event(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        username = kwargs.get("username", args[0] if len(args) > 0 else "")
        status = "failure"
        try:
            res = func(*args, **kwargs)
            if res:
                status = "success"
            return res
        except Exception:
            raise
        finally:
            log_entry = {
                "event": "login",
                "user": username,
                "result": status,
                "timestamp": datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "args": [str(a) for a in args],
                "kwargs": {k: str(v) for k, v in kwargs.items()},
            }
            try:
                logs = []
                if os.path.exists(LOG_JSON):
                    with open(LOG_JSON, "r", encoding="utf-8") as f:
                        try:
                            logs = json.load(f)
                        except json.JSONDecodeError:
                            logs = []
                logs.append(log_entry)
                with open(LOG_JSON, "w", encoding="utf-8") as f:
                    json.dump(logs, f, indent=4, ensure_ascii=False)
            except (FileNotFoundError, PermissionError, IOError) as e:
                print(f"Помилка запису логів: {e}")

    return wrapper


@log_event
def login(username: str, password: str, users_db: list) -> bool:
    if not username or not password:
        raise ValueError("Логін та пароль є обов'язковими для заповнення")

    target_hash = generate_hash(password, SALT)
    for u, h in users_db:
        if u == username and h == target_hash:
            return True
    return False


def run_task3():
    print("=" * 60)
    print("Завдання 3: Хешування, CSV-база та JSON-логування")
    print("=" * 60)

    try:
        create_users(users_to_register)
        db = read_users_db()

        print(f"{'Користувач':<18} | {'Хеш пароля (SHA3-256)'}")
        print("-" * 60)
        for u, h in db:
            print(f"{u:<18} | {h[:32]}...")

        print("\nПеревірка авторизації:")
        test_success = login(
            "admin_usr", "AdminStrongP@ss14", users_db=db
        )
        print(f"Спроба входу admin_usr: {test_success}")

        test_fail = login("admin_usr", "WrongPassword14", users_db=db)
        print(f"Спроба входу admin_usr (невірний пароль): {test_fail}")

    except (ValidationError, ValueError) as err:
        print(f"Помилка валідації: {err}")
    except (FileNotFoundError, PermissionError, IOError) as err:
        print(f"Помилка роботи з файлами: {err}")


if __name__ == "__main__":
    run_task3()