import csv
import datetime
import functools
import hashlib
import json
import os
import sys

# Додаю шлях до кореня проєкту, щоб імпортувати дані студента
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from shared.student import VARIANT_NUMBER

# Налаштовую шляхи до папки data та файлів бази користувачів і логів
DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "data")
)
USERS_CSV = os.path.join(DATA_DIR, "users.csv")
LOG_JSON = os.path.join(DATA_DIR, "log.json")

# Мінімальна довжина пароля для варіанту
MIN_PASSWORD_LENGTH = 14

# Сіль: доповнюю номер варіанту зліва нулями до 5 символів (для 28 буде '00028')
SALT = str(VARIANT_NUMBER).zfill(5)

# Список із 10 користувачів для реєстрації (логін, валідний пароль)
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


# Створюю власний клас винятку для помилок валідації пароля
class ValidationError(Exception):
    pass


# Функція генерації хешу пароля з сіллю
def generate_hash(password: str, salt: str = "00000") -> str:
    # Перевіряю, чи пароль або сіль не порожні
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми")
    
    # Перевіряю, чи довжина пароля відповідає мінімальній вимозі
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Довжина пароля має бути не менше {MIN_PASSWORD_LENGTH} символів"
        )
    
    # Зклеюю пароль із сіллю та рахую хеш за алгоритмом sha3_256
    salted = password + salt
    return hashlib.sha3_256(salted.encode("utf-8")).hexdigest()


# Створюю запис юзера: повертаю кортеж (логін, хеш)
def create_user(username: str, password: str) -> tuple:
    hash_val = generate_hash(password, SALT)
    return (username, hash_val)


# Функція для запису користувачів у файл users.csv
def create_users(users_list):
    try:
        # Автоматично створюю папку data, якщо її немає
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Відкриваю CSV файл на запис і додаю заголовок та кожного користувача
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password_hash"])
            for u, p in users_list:
                user_record = create_user(u, p)
                writer.writerow(user_record)
    except (FileNotFoundError, PermissionError, IOError) as e:
        # Перехоплюю системні помилки роботи з файлами
        print(f"Помилка створення файлу бази даних: {e}")


# Функція для читання збереженої бази даних із CSV файлу
def read_users_db():
    users_db = []
    try:
        with open(USERS_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Пропускаю заголовок таблиці (username, password_hash)
            for row in reader:
                if row:
                    users_db.append(tuple(row))
    except (FileNotFoundError, PermissionError, IOError) as e:
        print(f"Помилка читання бази даних: {e}")
    return users_db


# Декоратор для логування кожної спроби входу у файл log.json
def log_event(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Дістаю логін користувача з аргументів виклику
        username = kwargs.get("username", args[0] if len(args) > 0 else "")
        status = "failure"
        
        # Виконую саму функцію login і фіксую результат
        try:
            res = func(*args, **kwargs)
            if res:
                status = "success"
            return res
        except Exception:
            raise
        finally:
            # Формую словник події з точним часом, статусом та аргументами
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
            
            # Дописую новий запис до вже наявного масиву в log.json
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


# Функція аутентифікації користувача (обгорнута декоратором)
@log_event
def login(username: str, password: str, users_db: list) -> bool:
    # Забороняю порожній логін або пароль
    if not username or not password:
        raise ValueError("Логін та пароль є обов'язковими для заповнення")

    # Рахую хеш введеного пароля з моєю сіллю
    target_hash = generate_hash(password, SALT)
    
    # Шукаю, чи є запис з таким логіном і чи збігається хеш
    for u, h in users_db:
        if u == username and h == target_hash:
            return True
    return False


# Головна функція для виконання третього завдання
def run_task3():
    print("=" * 60)
    print("Завдання 3: Хешування, CSV-база та JSON-логування")
    print("=" * 60)

    try:
        # Створюю базу в CSV і зчитую її назад для перевірки
        create_users(users_to_register)
        db = read_users_db()

        # Виводжу перших користувачів та їхні хеші в консоль
        print(f"{'Користувач':<18} | {'Хеш пароля (SHA3-256)'}")
        print("-" * 60)
        for u, h in db:
            print(f"{u:<18} | {h[:32]}...")

        # Тестую успішний вхід з правильним паролем
        print("\nПеревірка авторизації:")
        test_success = login(
            "admin_usr", "AdminStrongP@ss14", users_db=db
        )
        print(f"Спроба входу admin_usr: {test_success}")

        # Тестую невдалий вхід із неправильним паролем
        test_fail = login("admin_usr", "WrongPassword14", users_db=db)
        print(f"Спроба входу admin_usr (невірний пароль): {test_fail}")

    # Обробка помилок валідації паролів та системних збоїв файлів
    except (ValidationError, ValueError) as err:
        print(f"Помилка валідації: {err}")
    except (FileNotFoundError, PermissionError, IOError) as err:
        print(f"Помилка роботи з файлами: {err}")


# Точка входу: запуск завдання напряму
if __name__ == "__main__":
    run_task3()