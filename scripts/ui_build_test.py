import asyncio
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import app.database as db
from app.message_bar import MessageBar


class StubSession(dict):
    def get(self, key, default=None):
        return dict.get(self, key, default)

    def set(self, key, value):
        dict.__setitem__(self, key, value)

    def remove(self, key):
        if key in self:
            del self[key]

    @property
    def store(self):
        return self


class StubWindow:
    def __init__(self):
        self.width = 800
        self.height = 600


class StubPage:
    def __init__(self):
        self.session = StubSession(
            lang="ar", theme_mode="dark", currency="MAD",
            user_id=1, user_name="Admin")
        self.window = StubWindow()
        self.views = []
        self.controls = []
        self.theme = None
        self.rtl = False
        self.fonts = {}
        self.navigation_bar = None
        self.msg_bar = MessageBar(self)
        self._dialog_count = 0

    def update(self):
        return None

    def show_dialog(self, dialog):
        self._dialog_count += 1
        return None

    def pop_dialog(self):
        self._dialog_count = max(0, self._dialog_count - 1)
        return None

    def run_task(self, coro, *args):
        return None


def main():
    tmp = os.path.join(tempfile.gettempdir(), "eshop_ui_test.db")
    if os.path.exists(tmp):
        os.remove(tmp)
    db.DB_PATH = tmp
    db.init_db()
    uid = db.create_user("Admin", "a@a.ma", "1234")
    db.add_product(uid, "Lait 1L", 20, 9.5, 7.0, category="laiticult",
                   barcode="ED12345678")
    p2 = db.add_product(uid, "Pain", 3, 1.5, 1.0, category="boulangerie")
    cid = db.add_customer(uid, "Ahmed", "0600")
    cn, ok, _ = db.add_credit_note(uid, cid,
                                   [(p2, "Pain", 2, 1.5, 3.0)])
    assert ok
    db.add_transaction(uid, "income", 50, "Sale", "test")

    page = StubPage()

    import flet as ft

    from app.screens.dashboard_screen import DashboardScreen
    from app.screens.stock_screen import StockScreen
    from app.screens.cash_screen import CashScreen
    from app.screens.credit_screen import CreditScreen
    from app.screens.settings_screen import SettingsScreen
    from app.screens.login_screen import LoginScreen
    from app import theme as T

    page.theme = T.AppTheme.get_theme("dark", "ar")

    # login (register path already has a user -> login mode)
    login = LoginScreen(page, on_login_success=lambda: None)
    c = login.build()
    assert isinstance(c, ft.Column)
    # register path
    db2 = db
    page.session.remove("user_id")  # not needed

    dash = DashboardScreen(page)
    assert isinstance(dash.build(), ft.Column)
    stock = StockScreen(page)
    assert isinstance(stock.build(), ft.Column)

    cash = CashScreen(page, on_rebuild=lambda: None)
    assert isinstance(cash.build(), ft.Column)
    credit = CreditScreen(page, on_rebuild=lambda: None)
    assert isinstance(credit.build(), ft.Column)

    settings = SettingsScreen(page, on_rebuild=lambda: None,
                              on_logout=lambda: None)
    assert isinstance(settings.build(), ft.Column)

    # dialogs
    stock._open_product_dialog(None)
    stock._open_sell(db.get_product(1))
    stock._open_credit_sell(db.get_product(1))
    stock._open_movement(db.get_product(1), "in")
    stock._open_history(db.get_product(1))
    stock._open_print_dialog()
    stock._open_delete(db.get_product(1))

    cash._open_add_dialog()
    credit._open_add_note()
    credit._open_detail(cn)
    credit._open_payment(db.get_credit_note(cn), credit._add_note_dialog)
    settings._confirm_logout()

    # main app boot (stub surface)
    import main as mainmod
    app = mainmod.eShopApp(page)
    app._show_login()
    app._show_main()
    app._update_screen(1)
    app._update_screen(2)
    app._update_screen(3)
    app._update_screen(4)

    print("UI BUILD TEST ALL PASS; dialogs shown:", page._dialog_count)
    os.remove(tmp)


if __name__ == "__main__":
    main()