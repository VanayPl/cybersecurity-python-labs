import os
import random
import sys

# Додаю кореневу папку проєкту в шляхи пошуку Python, щоб бачити модуль shared
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

# Імпортую ім'я студента та номер варіанта з файлу student.py
from shared.student import STUDENT_NAME, VARIANT_NUMBER

# Початковий список паролів для перевірки з мого варіанту
passwords = [
    "Compli4nc3@Check",
    "weak",
    "Risk@Ass3ssment",
    "guest",
    "Vulner4bility@Scan",
    "temp",
    "P3netration@Test",
    "demo",
    "S3curity@Audit",
    "trial",
]

# Критерії надійності: мінімальна довжина та обов'язкові типи символів
criteria = {
    "min_length": 8,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

# Множина заборонених (банальних) паролів
forbidden_passwords = {"weak", "guest", "temp", "demo", "trial", "password"}

# Набір спеціальних знаків для окремої перевірки
special_chars = set("!@#$%^&*()-_=+[]{}|;:,.<>?")


# Функція визначення категорії надійності для одного пароля
def evaluate_password(password, full_list):
    # Якщо пароль є у заборонених або занадто короткий — він одразу "Заборонений"
    if (
        password in forbidden_passwords
        or len(password) < criteria["min_length"]
    ):
        return "Заборонений"

    # Перевіряю наявність цифр, великих і малих літер, а також спецсимволів
    has_digit = any(char.isdigit() for char in password)
    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)
    has_special = any(char in special_chars for char in password)

    # Змінна True, якщо виконані всі 4 критерії за типами символів
    all_criteria = has_digit and has_upper and has_lower and has_special

    # Якщо виконані всі типи символів:
    if all_criteria:
        # Рахую, скільки разів пароль зустрічається у списку (1 = унікальний)
        is_unique = full_list.count(password) == 1
        # Якщо довший за норму на 4+ символи і унікальний — це "Дуже сильний"
        if (
            len(password) >= criteria["min_length"] + 4
            and is_unique
        ):
            return "Дуже сильний"
        # Якщо дублюється або коротший — просто "Сильний"
        return "Сильний"

    # Якщо виконано хоча б один критерій безпеки:
    if (
        has_digit
        or has_upper
        or has_lower
        or has_special
    ):
        # Якщо довжина достатня, але частину критеріїв пропущено — "Середній"
        if len(password) >= criteria["min_length"]:
            return "Середній"
        # Якщо коротший — "Слабкий"
        return "Слабкий"

    # Якщо жоден критерій не підійшов — "Слабкий"
    return "Слабкий"


# Головна функція запуску завдання 1
def run_task1():
    # Виводжу шапку з моїми даними
    print("=" * 60)
    print(f"Студент: {STUDENT_NAME}, Варіант: {VARIANT_NUMBER}")
    print("Завдання 1: Аналізатор надійності паролів")
    print("=" * 60)

    # Роблю копію списку паролів, щоб не псувати оригінал
    work_list = list(passwords)

    # Генерую 3 випадкові індекси зі списку
    random_indices = [
        random.randint(0, len(work_list) - 1) for _ in range(3)
    ]

    # Додаю обрані випадкові паролі в кінець списку (робимо повтори)
    for idx in random_indices:
        work_list.append(work_list[idx])

    # Виводжу заголовки стовпців таблиці
    print(f"{'№':<4} | {'Пароль':<24} | {'Категорія'}")
    print("-" * 60)

    # Проходжу по кожному паролю, оцінюю його категорію і друкую рядок
    for i, pwd in enumerate(work_list, start=1):
        category = evaluate_password(pwd, work_list)
        print(f"{i:<4} | {pwd:<24} | {category}")


# Запускаю завдання, якщо файл запускається напряму
if __name__ == "__main__":
    run_task1()