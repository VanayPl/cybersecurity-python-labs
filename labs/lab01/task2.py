import os
import sys

# Додаю шлях до кореня проєкту, щоб бачити спільну папку shared
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

# Імпортую ім'я та варіант із файлу student.py
from shared.student import STUDENT_NAME, VARIANT_NUMBER

# База користувачів: вказую їхню посаду, рівень допуску (clearance), відділ та статус активності
users = {
    "ai_security_expert": {
        "role": "ai_security",
        "clearance": 4,
        "department": "AI Security",
        "active": True,
    },
    "ml_engineer": {
        "role": "ml_engineer",
        "clearance": 3,
        "department": "Machine Learning",
        "active": True,
    },
    "data_engineer": {
        "role": "data_engineer",
        "clearance": 2,
        "department": "Data Engineering",
        "active": True,
    },
    "research_assistant": {
        "role": "researcher",
        "clearance": 2,
        "department": "Research",
        "active": True,
    },
    "training_bot": {
        "role": "bot_account",
        "clearance": 1,
        "department": "Automation",
        "active": False,
    },
}

# Список ресурсів компанії та потрібний числовий рівень безпеки для кожного (від 1 до 4)
resources = [
    ("ai_models", 4),
    ("training_datasets", 3),
    ("data_pipelines", 2),
    ("research_notebooks", 2),
    ("model_artifacts", 4),
    ("synthetic_data", 1),
    ("adversarial_tests", 3),
    ("model_registry", 4),
    ("feature_stores", 2),
    ("public_models", 1),
]

# Текстові назви для рівнів доступу від 1 до 4
security_levels = (
    "Open Source",
    "Internal Research",
    "Proprietary",
    "Trade Secret",
)

# Список заблокованих акаунтів (множина для швидкого пошуку)
blocked_users = {"training_bot", "model_theft", "data_poisoning_acc"}


# Функція, яка вирішує: пускати користувача до ресурсу чи ні
def check_access(username, resource_level):
    # Якщо такого юзера взагалі немає в системі — відмова
    if username not in users:
        return "DENY (User not found)"

    # Якщо юзер є в списку заблокованих — відмова
    if username in blocked_users:
        return "DENY (User is blocked)"

    # Отримую дані юзера і дивлюся, чи акаунт активний
    user_info = users[username]
    if not user_info.get("active", False):
        return "DENY (Account inactive)"

    # Якщо рівень допуску користувача більший або дорівнює рівню ресурсу — пускаю
    if user_info["clearance"] >= resource_level:
        return "ALLOW"
    
    # Якщо допуску не вистачає — відмова
    return "DENY (Insufficient clearance)"


# Головна функція для виконання другого завдання
def run_task2():
    # Друк шапки звіту
    print("=" * 60)
    print(f"Студент: {STUDENT_NAME}, Варіант: {VARIANT_NUMBER}")
    print("Завдання 2: Багаторівнева система контролю доступу")
    print("=" * 60)

    # Виводжу всі ресурси та перетворюю числові рівні на зрозумілі назви
    print("\nСписок ресурсів системи:")
    for res_name, res_lvl in resources:
        # Віднімаю 1 від рівня, бо індексація списку починається з 0
        lvl_name = security_levels[res_lvl - 1]
        print(f"Ресурс: {res_name:<22} | Рівень: {lvl_name} ({res_lvl})")

    # Перевіряю доступ кожного користувача до кожного наявного ресурсу
    print("\nРезультати перевірки доступу:")
    for user in users:
        for res_name, res_lvl in resources:
            result = check_access(user, res_lvl)
            print(f"user={user} resource={res_name} -> {result}")


# Точка входу: запуск завдання, якщо запускати файл напряму
if __name__ == "__main__":
    run_task2()