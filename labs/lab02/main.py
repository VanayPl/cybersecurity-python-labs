"""Головний модуль запуску Лабораторної роботи №2 (Варіант 13).

Підтримує дві основні підкоманди:
- demo: запуск демонстраційного сценарію Завдання 1 (ООП, автентифікація, сесії, аудит).
- analyze: запуск утиліти кібербезпеки Завдання 2 (Сканер витоків PII).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

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

    # Підкоманда demo
    subparsers.add_parser(
        "demo",
        help="Запустити демонстрацію об'єктно-орієнтованої системи (Завдання 1)",
    )

    # Підкоманда analyze
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
