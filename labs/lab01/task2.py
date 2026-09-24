import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from shared.student import STUDENT_NAME, VARIANT_NUMBER

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

security_levels = (
    "Open Source",
    "Internal Research",
    "Proprietary",
    "Trade Secret",
)
blocked_users = {"training_bot", "model_theft", "data_poisoning_acc"}


def check_access(username, resource_level):
    if username not in users:
        return "DENY (User not found)"

    if username in blocked_users:
        return "DENY (User is blocked)"

    user_info = users[username]
    if not user_info.get("active", False):
        return "DENY (Account inactive)"

    if user_info["clearance"] >= resource_level:
        return "ALLOW"
    return "DENY (Insufficient clearance)"


def run_task2():
    print("=" * 60)
    print(f"Студент: {STUDENT_NAME}, Варіант: {VARIANT_NUMBER}")
    print("Завдання 2: Багаторівнева система контролю доступу")
    print("=" * 60)

    print("\nСписок ресурсів системи:")
    for res_name, res_lvl in resources:
        lvl_name = security_levels[res_lvl - 1]
        print(f"Ресурс: {res_name:<22} | Рівень: {lvl_name} ({res_lvl})")

    print("\nРезультати перевірки доступу:")
    for user in users:
        for res_name, res_lvl in resources:
            result = check_access(user, res_lvl)
            print(f"user={user} resource={res_name} -> {result}")


if __name__ == "__main__":
    run_task2()