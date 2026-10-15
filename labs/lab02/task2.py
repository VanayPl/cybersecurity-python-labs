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
import json
import logging
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("pii_scanner")

# Регулярні вирази для пошуку типів PII
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
            # Email
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

            # Credit Card
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

            # Phone Numbers
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

            # IPv4
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
