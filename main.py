import logging
import os

import flet as ft

from app import responsive
from app import theme as T
from app import version as V
from app.activity import log_action
from app.database import init_db
from app.loading import LoadingDots
from app.logging_config import configure_logging, get_logger
from app.message_bar import MessageBar
from app.screens.cash_screen import CashScreen
from app.screens.credit_screen import CreditScreen
from app.screens.dashboard_screen import DashboardScreen
from app.screens.login_screen import LoginScreen
from app.screens.settings_screen import SettingsScreen
from app.screens.stock_screen import StockScreen
from app.translations import LANG_LABELS, SUPPORTED_LANGS, t

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

NAV_ITEMS = [
    (ft.Icons.DASHBOARD_OUTLINED, ft.Icons.DASHBOARD, "nav_dashboard"),
    (ft.Icons.INVENTORY_2_OUTLINED, ft.Icons.INVENTORY_2, "nav_stock"),
    (ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
     ft.Icons.ACCOUNT_BALANCE_WALLET, "nav_cash"),
    (ft.Icons.CREDIT_CARD_OUTLINED, ft.Icons.CREDIT_CARD, "nav_credit"),
    (ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS, "nav_settings"),
]

def _find_font(filename):
    # Only bundled fonts need registering with Flet; system fonts are
    # usable by family name without bundling, so only search assets.
    ext = os.path.splitext(os.path.basename(filename))[1]
    search = "".join(
        ch for ch in os.path.splitext(os.path.basename(filename))[0]
        if ch.isalnum()).lower()
    d = os.path.join(ASSETS_DIR, "fonts")
    if not os.path.isdir(d):
        return None
    try:
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith(ext.lower()):
                key = "".join(
                    ch for ch in os.path.splitext(fn)[0]
                    if ch.isalnum()).lower()
                if search in key:
                    return os.path.join(d, fn)
    except OSError:
        return None
    return None


logger = get_logger("app.main")


class eShopApp:
    def __init__(self, page):
        self.page = page
        self.tab = 0
        self.view = ft.View(route="/", padding=0)
        page.views.append(self.view)
        page.title = f"{V.APP_NAME} v{V.VERSION}"
        try:
            page.window.width = 420
            page.window.height = 800
            page.window.min_width = 320
            page.window.min_height = 520
        except Exception:
            logger.debug("window sizing not supported", exc_info=True)
        page.on_resize = self._on_resize
        init_db()

        self.page.msg_bar = MessageBar(page)
        self.nav = self._build_nav()
        self._show_nav = False
        self._loading = None
        self._current_screen_obj = None
        self._apply_session_defaults()
        self._register_font()
        self._apply_theme()
        self._apply_rtl()

    # ------------------------------------------------------------------
    def _register_font(self):
        fonts = {}
        for family, file in ((T.ARABIC_FONT, "VIPRawyThinThin.ttf"),
                             (T.LATIN_FONT, "Comfortaa-Regular.ttf")):
            path = _find_font(file)
            if not path:
                continue
            fonts[family] = "/fonts/" + os.path.basename(path)
        if fonts:
            try:
                self.page.fonts = fonts
            except Exception:
                logger.debug("font registration failed", exc_info=True)

    def _apply_session_defaults(self):
        for key, default in (("lang", "ar"), ("theme_mode", "dark"),
                             ("currency", "MAD")):
            if not self.page.session.store.get(key):
                self.page.session.store.set(key, default)

    def _apply_rtl(self):
        try:
            self.page.rtl = (self.page.session.store.get("lang") or "ar") == "ar"
        except Exception:
            logger.debug("rtl apply failed", exc_info=True)

    def _apply_theme(self):
        mode = self.page.session.store.get("theme_mode") or "dark"
        lang = self.page.session.store.get("lang") or "ar"
        try:
            self.page.theme = T.AppTheme.get_theme(mode, lang)
        except Exception:
            logger.debug("theme apply failed", exc_info=True)

    def _build_nav(self):
        return ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ic, selected_icon=sic,
                                            label=t(self.page, key))
                for ic, sic, key in NAV_ITEMS
            ],
            selected_index=self.tab,
            on_change=self._on_nav_change,
        )

    def _build_rail(self):
        return ft.NavigationRail(
            destinations=[
                ft.NavigationRailDestination(icon=ic, selected_icon=sic,
                                             label=t(self.page, key))
                for ic, sic, key in NAV_ITEMS
            ],
            selected_index=self.tab,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=88,
            group_alignment=-0.7,
            on_change=self._on_nav_change,
        )

    # ------------------------------------------------------------------
    def run(self):
        self._show_splash()
        self.page.run_task(self._after_splash, 1.8)

    async def _after_splash(self, seconds):
        import asyncio

        await asyncio.sleep(seconds)
        if self._loading is not None:
            self._loading.stop()
        try:
            if self.page.session.store.get("user_id"):
                self._show_main()
            else:
                self._show_login()
        except Exception:
            logger.exception("failed to restore session")

    # ------------------------------------------------------------------
    def _set_content(self, content, center=False, footer=True):
        pad = responsive.content_padding(self.page)
        if center:
            body = ft.Container(
                content=content,
                expand=True,
                alignment=ft.Alignment.CENTER,
                padding=pad,
            )
        else:
            body = ft.Container(content=content, expand=True, padding=pad)
        controls = [body]
        if footer:
            controls.append(self._build_bottom_bar())
        column = ft.Column(controls=controls, spacing=0, expand=True)
        if self._show_nav and responsive.wide(self.page):
            new_controls = [
                ft.Row(
                    controls=[
                        self._build_rail(),
                        ft.VerticalDivider(width=1),
                        column,
                    ],
                    spacing=0,
                    expand=True,
                )
            ]
        else:
            new_controls = [column]
        self.view.controls = new_controls
        self.page.update()

    def _on_resize(self, e):
        if not self._show_nav:
            return
        self.page.run_task(self._refresh_after_resize, 0.2)

    async def _refresh_after_resize(self, seconds):
        import asyncio

        await asyncio.sleep(seconds)
        try:
            self._update_screen(self.tab)
        except Exception:
            logger.debug("resize refresh failed", exc_info=True)

    def _build_bottom_bar(self):
        dark = (self.page.session.store.get("theme_mode") or "dark") == "dark"
        surface = T.SURFACE_DARK if dark else T.SURFACE_LIGHT
        lang = self.page.session.store.get("lang") or "ar"

        lang_buttons = ft.SegmentedButton(
            segments=[
                ft.Segment(value=lg, label=ft.Text(LANG_LABELS[lg], size=11))
                for lg in SUPPORTED_LANGS
            ],
            selected=[lang],
            show_selected_icon=False,
            padding=4,
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            ),
            on_change=self._on_bottom_lang_change,
        )
        version_badge = ft.Container(
            content=ft.Text(
                f"{t(self.page, 'version')} {V.VERSION}",
                size=12,
                weight=ft.FontWeight.W_600,
                color=T.WARNING,
            ),
            bgcolor=f"{T.WARNING}22",
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        expand=2,
                    ),
                    ft.Container(
                        content=lang_buttons,
                        expand=6,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Container(
                        content=version_badge,
                        expand=2,
                        alignment=ft.Alignment.CENTER_RIGHT,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(16, 8, 16, 8),
            bgcolor=surface,
            border_radius=ft.BorderRadius(14, 14, 0, 0),
        )

    def _set_lang(self, lang):
        self.page.session.store.set("lang", lang)
        log_action(self.page, "language_change", f"lang={lang}")
        self._apply_rtl()
        self._apply_theme()
        if self._show_nav:
            self._update_screen(self.tab)
        else:
            self._show_login()

    def _on_bottom_lang_change(self, e):
        data = e.data
        if isinstance(data, list) and len(data) > 0:
            lang = data[0]
        elif isinstance(data, str) and data:
            lang = data
        else:
            lang = e.control.selected[0] if e.control.selected else "ar"
        self._set_lang(lang)

    def _show_splash(self):
        self.view.navigation_bar = None
        self._show_nav = False
        gif = os.path.join(ASSETS_DIR, "loading.gif")
        spinner = (
            ft.Image(src=gif, width=120, height=120)
            if os.path.exists(gif)
            else ft.ProgressRing(width=70, height=70, stroke_width=5)
        )
        self._loading = LoadingDots(self.page)
        splash = ft.Stack(
            controls=[
                ft.Column(
                    controls=[spinner],
                    expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self._loading.build(),
                            ft.Text(V.APP_NAME, size=30,
                                    weight=ft.FontWeight.W_700,
                                    color=T.PRIMARY),
                            ft.Text(f"v{V.VERSION}", size=13,
                                    color="#888888"),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.Alignment(0, 1),
                    padding=ft.Padding.only(bottom=28, left=16, right=16),
                    expand=True,
                ),
            ],
            expand=True,
        )
        self._set_content(splash, center=False, footer=False)
        self._loading.start()

    def _show_login(self):
        self.view.navigation_bar = None
        self._show_nav = False
        self.tab = 0
        screen = LoginScreen(
            self.page,
            on_login_success=self._show_main,
        )
        self._current_screen_obj = screen
        self._set_content(screen.build(), center=True)

    # ------------------------------------------------------------------
    def _show_main(self):
        self.page.session.store.set("has_session", True)
        self.tab = 0
        self._show_nav = True
        self._update_screen(0)

    def _on_nav_change(self, e):
        self.tab = e.control.selected_index
        log_action(self.page, "nav", f"tab={self.tab}")
        self._update_screen(self.tab)

    def _update_screen(self, index):
        self.nav = self._build_nav()
        self.view.navigation_bar = (
            None if responsive.wide(self.page) else self.nav
        )
        try:
            self.nav.selected_index = index
        except Exception:
            logger.debug("nav index selection failed", exc_info=True)

        if index == 0:
            screen = DashboardScreen(self.page)
        elif index == 1:
            screen = StockScreen(self.page)
        elif index == 2:
            screen = CashScreen(self.page, on_rebuild=self._refresh_main)
        elif index == 3:
            screen = CreditScreen(self.page, on_rebuild=self._refresh_main)
        else:
            screen = SettingsScreen(self.page, on_rebuild=self._refresh_main,
                                    on_logout=self._logout)
        self._current_screen_obj = screen
        self._set_content(screen.build())

    def _refresh_main(self):
        self._apply_rtl()
        self._apply_theme()
        if self._show_nav:
            self._update_screen(self.tab)
        elif self._current_screen_obj is not None:
            self._set_content(self._current_screen_obj.build())

    def _logout(self):
        log_action(self.page, "logout")
        for key in ("user_id", "user_name", "has_session"):
            self.page.session.store.remove(key)
        self.view.navigation_bar = None
        self._show_login()


def main(page):
    configure_logging()
    logger.info("app started version=%s build=%s", V.VERSION, V.BUILD_DATE)
    app = eShopApp(page)
    app.run()


if __name__ == "__main__":
    ft.run(main, name="eShop", assets_dir="assets")
