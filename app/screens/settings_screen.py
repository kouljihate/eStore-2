import flet as ft

from app import theme as T
from app.activity import log_action
from app.currency import CURRENCIES
from app.translations import LANG_LABELS, SUPPORTED_LANGS, t


class SettingsScreen:
    def __init__(self, page, on_rebuild=None, on_logout=None):
        self.page = page
        self.on_rebuild = on_rebuild
        self.on_logout = on_logout
        self.msg_bar = page.msg_bar

    def build(self):
        lang = self.page.session.store.get("lang") or "ar"
        theme_mode = self.page.session.store.get("theme_mode") or "dark"
        currency = self.page.session.store.get("currency") or "MAD"

        theme_buttons = ft.SegmentedButton(
            segments=[
                ft.Segment(value="light",
                           label=ft.Row(controls=[
                               ft.Icon(ft.Icons.LIGHT_MODE, size=16),
                               ft.Text(t(self.page, "theme_light")),
                           ], spacing=4)),
                ft.Segment(value="dark",
                           label=ft.Row(controls=[
                               ft.Icon(ft.Icons.DARK_MODE, size=16),
                               ft.Text(t(self.page, "theme_dark")),
                           ], spacing=4)),
            ],
            selected=[theme_mode],
            on_change=lambda e: self._set_theme(e),
        )

        lang_buttons = ft.SegmentedButton(
            segments=[
                ft.Segment(value=lg, label=ft.Text(LANG_LABELS[lg]))
                for lg in SUPPORTED_LANGS
            ],
            selected=[lang],
            on_change=lambda e: self._set_lang(e),
        )

        currency_dropdown = ft.Dropdown(
            label=t(self.page, "currency"),
            options=[
                ft.dropdown.Option(code, f"{CURRENCIES[code]['symbol']} {code}")
                for code in CURRENCIES
            ],
            value=currency if currency in CURRENCIES else "MAD",
            dense=True,
            border_radius=8,
            on_select=lambda e: self._set_currency(e),
        )

        def section(title, control):
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(title, size=16, weight=ft.FontWeight.W_600),
                        control,
                    ],
                    spacing=8,
                ),
                padding=16,
                bgcolor=(T.SURFACE_DARK if (theme_mode == "dark")
                         else T.SURFACE_LIGHT),
                border_radius=14,
            )

        return ft.Column(
            controls=[
                ft.Text(t(self.page, "settings_title"), size=22,
                        weight=ft.FontWeight.W_700),
                section(t(self.page, "theme"), theme_buttons),
                section(t(self.page, "language"), lang_buttons),
                section(t(self.page, "currency"), currency_dropdown),
                ft.FilledButton(
                    content=t(self.page, "logout"),
                    icon=ft.Icons.LOGOUT,
                    height=48,
                    on_click=lambda e: self._confirm_logout(),
                ),
                self.msg_bar,
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _set_theme(self, e):
        value = e.control.selected[0] if e.control.selected else "dark"
        self.page.session.store.set("theme_mode", value)
        log_action(self.page, "theme_change", f"mode={value}")
        if self.on_rebuild:
            self.on_rebuild()

    def _set_lang(self, e):
        value = e.control.selected[0] if e.control.selected else "ar"
        self.page.session.store.set("lang", value)
        log_action(self.page, "language_change", f"lang={value}")
        try:
            self.page.rtl = value == "ar"
        except Exception:
            pass
        if self.on_rebuild:
            self.on_rebuild()

    def _set_currency(self, e):
        value = e.control.value or "MAD"
        if value not in CURRENCIES:
            value = "MAD"
        self.page.session.store.set("currency", value)
        log_action(self.page, "currency_change", f"currency={value}")
        if self.on_rebuild:
            self.on_rebuild()
        self.msg_bar.show_success(t(self.page, "settings_saved"))

    def _confirm_logout(self):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(t(self.page, "logout")),
            content=ft.Text(t(self.page, "logout_confirm")),
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(dialog)),
                ft.FilledButton(
                    t(self.page, "logout"),
                    style=ft.ButtonStyle(bgcolor=T.ERROR),
                    on_click=lambda e: self._do_logout(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def _do_logout(self, dialog):
        self._close(dialog)
        if self.on_logout:
            self.on_logout()

    def _close(self, dialog):
        try:
            self.page.pop_dialog()
        except Exception:
            dialog.open = False
            self.page.update()