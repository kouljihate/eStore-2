import flet as ft

from app import responsive
from app import theme as T
from app.activity import log_action
from app.currency import format_currency, get_currency_code
from app.database import add_transaction, get_dashboard_data, get_transactions
from app.translations import t, tx_category_label


class CashScreen:
    def __init__(self, page, on_rebuild=None):
        self.page = page
        self.on_rebuild = on_rebuild
        self.msg_bar = getattr(page, "msg_bar", None)
        self.uid = page.session.store.get("user_id")

    def _uid(self):
        uid = self.page.session.store.get("user_id")
        self.uid = uid
        return uid

    def _surface(self):
        dark = (self.page.session.store.get("theme_mode") or "dark") == "dark"
        return T.SURFACE_DARK if dark else T.SURFACE_LIGHT

    def build(self):
        uid = self._uid()
        cur = get_currency_code(self.page)
        data = get_dashboard_data(self.uid)
        balance = data["cash_balance"]

        balance_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(t(self.page, "balance"), size=14,
                            color="#888888"),
                    ft.Text(
                        format_currency(balance, cur),
                        size=34, weight=ft.FontWeight.W_700,
                        color=T.SUCCESS if balance >= 0 else T.ERROR,
                        font_family=T.NUMBER_FONT,
                    ),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(t(self.page, "total_income"),
                                            size=12, color="#888888"),
                                    ft.Text(
                                        format_currency(data["cash_income"], cur),
                                        size=16, weight=ft.FontWeight.W_600,
                                        color=T.SUCCESS,
                                        font_family=T.NUMBER_FONT),
                                ],
                                expand=True,
                                spacing=2,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(t(self.page, "total_expenses"),
                                            size=12, color="#888888"),
                                    ft.Text(
                                        format_currency(data["cash_expense"], cur),
                                        size=16, weight=ft.FontWeight.W_600,
                                        color=T.ERROR,
                                        font_family=T.NUMBER_FONT),
                                ],
                                expand=True,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=2,
                            ),
                        ],
                        spacing=12,
                    ),
                ],
                spacing=6,
            ),
            padding=20,
            bgcolor=self._surface(),
            border_radius=14,
        )

        transactions = responsive.hscroll(
            self._transactions_table(get_transactions(self.uid, limit=50)),
            self.page,
        )

        controls = [
                ft.Row(
                    controls=[
                        ft.Text(t(self.page, "cash_title"), size=22,
                                weight=ft.FontWeight.W_700),
                        ft.Container(expand=True),
                        ft.FilledButton(
                            content=t(self.page, "add_transaction"),
                            icon=ft.Icons.ADD_CARD,
                            on_click=lambda e: self._open_add_dialog(),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                balance_card,
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(t(self.page, "transactions_title"), size=16,
                                    weight=ft.FontWeight.W_600),
                            transactions,
                        ],
                        spacing=10,
                    ),
                    padding=16,
                    bgcolor=self._surface(),
                    border_radius=14,
                ),
            ]
        if self.msg_bar is not None:
            controls.append(self.msg_bar)
        body = ft.Column(
            controls=controls,
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        return body

    def _transactions_table(self, rows):
        if not rows:
            return ft.Text(t(self.page, "no_transactions"), size=13, color="#888888")
        cur = get_currency_code(self.page)
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(t(self.page, "type"))),
                ft.DataColumn(ft.Text(t(self.page, "amount"))),
                ft.DataColumn(ft.Text(t(self.page, "category"))),
                ft.DataColumn(ft.Text(t(self.page, "description"))),
                ft.DataColumn(ft.Text(t(self.page, "date"))),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(
                            t(self.page, "income" if r["type"] == "income"
                              else "expense"),
                            size=13,
                            color=T.SUCCESS if r["type"] == "income" else T.ERROR,
                            weight=ft.FontWeight.W_600)),
                        ft.DataCell(ft.Text(
                            f"+{format_currency(r['amount'], cur)}"
                            if r["type"] == "income"
                            else f"-{format_currency(r['amount'], cur)}",
                            size=13,
                            color=T.SUCCESS if r["type"] == "income" else T.ERROR,
                            font_family=T.NUMBER_FONT)),
                        ft.DataCell(ft.Text(tx_category_label(self.page, r["category"]), size=13)),
                        ft.DataCell(ft.Text(r["description"] or "", size=12)),
                        ft.DataCell(ft.Text(r["date"] or "", size=11)),
                    ]
                )
                for r in rows
            ],
        )

    def _open_add_dialog(self):
        self.t_type = ft.Dropdown(
            label=t(self.page, "transaction_type"),
            options=[
                ft.dropdown.Option("income", t(self.page, "income")),
                ft.dropdown.Option("expense", t(self.page, "expense")),
            ],
            value="income",
            dense=True,
            border_radius=8,
        )
        self.t_amount = ft.TextField(
            label=t(self.page, "transaction_amount"),
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            border_radius=8,
            autofocus=True,
        )
        self.t_category = ft.TextField(
            label=t(self.page, "transaction_category"),
            dense=True,
            border_radius=8,
        )
        self.t_description = ft.TextField(
            label=t(self.page, "transaction_description"),
            dense=True,
            border_radius=8,
            multiline=True,
            min_lines=1,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(t(self.page, "add_transaction")),
            content=ft.Column(
                controls=[
                    self.t_type,
                    self.t_amount,
                    self.t_category,
                    self.t_description,
                ],
                spacing=10,
                width=responsive.dialog_width(self.page, 320),
            ),
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(dialog)),
                ft.FilledButton(t(self.page, "save"),
                                on_click=lambda e: self._do_add_transaction(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def _do_add_transaction(self, dialog):
        try:
            raw = (self.t_amount.value or "0").strip().replace(",", ".")
            amount = float(raw)
        except ValueError:
            amount = 0
        if amount <= 0:
            self.msg_bar.show_error(t(self.page, "invalid_amount"))
            return
        ttype = self.t_type.value or "income"
        if ttype not in ("income", "expense"):
            ttype = "income"
        category = (self.t_category.value or "").strip() or "General"
        description = (self.t_description.value or "").strip()
        uid = self._uid()
        if not add_transaction(uid, ttype, amount, category, description):
            self.msg_bar.show_error(t(self.page, "generic_error"))
            return
        log_action(self.page, "transaction_add",
                   f"type={ttype} amount={amount:g} category={category}")
        self.msg_bar.show_success(t(
            self.page, "income_success" if ttype == "income" else "expense_success"))
        self._close(dialog)
        if self.on_rebuild:
            self.on_rebuild()

    def _close(self, dialog):
        try:
            self.page.pop_dialog()
        except Exception:
            dialog.open = False
            self.page.update()