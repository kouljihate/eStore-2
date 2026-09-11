import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "app.log")

FILE_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
CONSOLE_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5

# Framework loggers kept quiet (WARNING+) so their debug/info noise stays
# out, while every warning/error still reaches our handlers.
NOISY_LOGGERS = (
    "flet",
    "flet_controls",
    "flet_object_patch",
    "flet_transport",
    "watchfiles",
    "asyncio",
)

_configured = False


def configure_logging(level=logging.INFO):
    global _configured
    if _configured:
        return
    _configured = True

    os.makedirs(LOGS_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        file_fmt = logging.Formatter(FILE_FORMAT, datefmt=DATE_FORMAT)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_fmt)
        root.addHandler(file_handler)

        console_fmt = logging.Formatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_fmt)
        root.addHandler(console_handler)

    for noisy in NOISY_LOGGERS:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Every interpreter-level failure path funnels into the log:
    # main thread, background threads, and unretrieved async errors.
    sys.excepthook = _excepthook
    threading.excepthook = _thread_excepthook
    try:
        sys.unraisablehook = _unraisable_hook
    except AttributeError:
        pass


def _excepthook(etype, value, tb):
    logging.getLogger("app").critical(
        "Uncaught exception", exc_info=(etype, value, tb)
    )


def _thread_excepthook(args):
    logging.getLogger("app").critical(
        "Uncaught thread exception in %s", args.thread.name,
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def _unraisable_hook(unraisable):
    logging.getLogger("app").critical(
        "Unraisable exception in %s", unraisable.object,
        exc_info=(unraisable.exc_type, unraisable.exc_value,
                  unraisable.exc_traceback),
    )


def get_logger(name="app"):
    return logging.getLogger(name)