import logging

_logger = logging.getLogger("app.actions")


def _uid_of(page):
    try:
        return page.session.store.get("user_id")
    except Exception:
        return None


def log_action(page_or_uid, action, details=""):
    """Log a user action/click to logs/app.log.

    Accepts either a Flet page (uid extracted from session) or a raw uid.
    Never raises — logging must not break UI flows.
    """
    try:
        if hasattr(page_or_uid, "session"):
            uid = _uid_of(page_or_uid)
        else:
            uid = page_or_uid
        extra = f" {details}" if details else ""
        _logger.info("action=%s user=%s%s", action, uid, extra)
    except Exception:
        pass
