import flet as ft

MOBILE_MAX = 600
TABLET_MAX = 1024


def viewport_width(page):
    try:
        return page.width or 0
    except Exception:
        return 0


def screen_size(page):
    w = viewport_width(page)
    if w < MOBILE_MAX:
        return "mobile"
    if w < TABLET_MAX:
        return "tablet"
    return "desktop"


def is_mobile(page):
    return screen_size(page) == "mobile"


def wide(page):
    return screen_size(page) in ("tablet", "desktop")


def content_padding(page):
    return 8 if is_mobile(page) else 16


def dialog_width(page, base):
    w = viewport_width(page)
    if w <= 0:
        return base
    return max(260, min(base, w - 48))


def hscroll(control, page):
    if is_mobile(page) and isinstance(control, ft.DataTable):
        return ft.Row(controls=[control], scroll=ft.ScrollMode.AUTO)
    return control