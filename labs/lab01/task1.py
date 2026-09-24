import os
import random
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from shared.student import STUDENT_NAME, VARIANT_NUMBER

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

criteria = {
    "min_length": 8,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {"weak", "guest", "temp", "demo", "trial", "password"}
special_chars = set("!@#$%^&*()-_=+[]{}|;:,.<>?")


def evaluate_password(password, full_list):
    if (
        password in forbidden_passwords
        or len(password) < criteria["min_length"]
    ):
        return "Заборонений"

    has_digit = any(char.isdigit() for char in password)
    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)
    has_special = any(char in special_chars for char in password)

    all_criteria = has_digit and has_upper and has_lower and has_special

    if all_criteria:
        is_unique = full_list.count(password) == 1
        if (
            len(password) >= criteria["min_length"] + 4
            and is_unique
        ):
            return "Дуже сильний"
        return "Сильний"

    if (
        has_digit
        or has_upper
        or has_lower
        or has_special
    ):
        if len(password) >= criteria["min_length"]:
            return "Середній"
        return "Слабкий"

    return "Слабкий"


def run_task1():
    print("=" * 60)
    print(f"Студент: {STUDENT_NAME}, Варіант: {VARIANT_NUMBER}")
    print("Завдання 1: Аналізатор надійності паролів")
    print("=" * 60)

    work_list = list(passwords)
    random_indices = [
        random.randint(0, len(work_list) - 1) for _ in range(3)
    ]
    for idx in random_indices:
        work_list.append(work_list[idx])

    print(f"{'№':<4} | {'Пароль':<24} | {'Категорія'}")
    print("-" * 60)
    for i, pwd in enumerate(work_list, start=1):
        category = evaluate_password(pwd, work_list)
        print(f"{i:<4} | {pwd:<24} | {category}")


if __name__ == "__main__":
    run_task1()