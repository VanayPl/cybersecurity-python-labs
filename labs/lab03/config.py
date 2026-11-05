"""Конфігурація та константи варіанта (Варіант 13: Реєстр ризиків хмарної конфігурації)."""

SUBJECT_AREA: str = "Реєстр ризиків хмарної конфігурації"
SUBJECT_DESCRIPTION: str = (
    "Сервіс обліку знахідок аудиту хмарної конфігурації. "
    "Категорія визначає напрям перевірки (iam, storage, network), "
    "value — навчальну оцінку ризику від 0.0 до 10.0, "
    "status — стан опрацювання знахідки."
)
VALUE_UNIT: str = "score"
THRESHOLD: float = 7.0
MIN_VALUE: float = 0.0
MAX_VALUE: float = 10.0

ALLOWED_CATEGORIES: tuple[str, ...] = ("iam", "storage", "network")
ALLOWED_STATUSES: tuple[str, ...] = ("new", "in_progress", "done")
RECORD_TITLE_PREFIX: str = "Знахідка хмарного аудиту"

DEFAULT_LIMIT: int = 20
MAX_LIMIT: int = 100
MAX_BATCH_SIZE: int = 100
