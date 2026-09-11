import logging
import os
import sys
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "app.log")

FILE_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
CONSOLE_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5

_configured = False


def configure_logging(level=logging.INFO):
    global _configured
    if _configured:
        return
    _configured = True

    os.makedirs(LOGS_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)
    if root.handlers:
        return

    file_fmt = logging.Formatter(FILE_FORMAT, datefmt=DATE_FORMAT)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(file_fmt)
    root.addHandler(file_handler)

    console_fmt = logging.Formatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_fmt)
    root.addHandler(console_handler)

    for noisy in ("flet", "watchfiles", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    sys.excepthook = _excepthook


def _excepthook(etype, value, tb):
    logging.getLogger("app").critical(
        "Uncaught exception", exc_info=(etype, value, tb)
    )


def get_logger(name="app"):
    return logging.getLogger(name)