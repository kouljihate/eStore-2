import flet as ft

from app import responsive
from app import theme as T
from app.currency import format_currency, get_currency_code
from app.database import (
    get_dashboard_data,
    get_stock_movements,
    get_transactions,
)
from app.translations import t, tx_category_label


class DashboardScreen:
    def __init__(self, page):
        self.page = page
        self.msg_bar = getattr(page, "msg_bar", None)

    def _kpi_card(self, label, value, icon, color, icon_bg=None):
        dark = (self.page.session.store.get("theme_mode") or "dark") == "dark"
        surface = T.SURFACE_DARK if dark else T.SURFACE_LIGHT
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=30),
                        bgcolor=f"{color}22",
                        border_radius=10,
                        padding=10,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(value, size=20, weight=ft.FontWeight.W_700,
                                    font_family=T.NUMBER_FONT),
                            ft.Text(label, size=12, color=color),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor=surface,
            border_radius=14,
        )

    def build(self):
        uid = self.page.session.store.get("user_id")
        if not uid:
            return ft.Column(
                controls=[ft.Text(t(self.page, "login_title"), size=16)],
                spacing=12,
                expand=True,
            )
        cur = get_currency_code(self.page)
        data = get_dashboard_data(uid)
        fmt = lambda v: format_currency(v, cur)

        movements = get_stock_movements(uid, limit=5)
        transactions = get_transactions(uid, limit=5)
        is_new = (data["product_count"] == 0 and data["cash_income"] == 0
                  and data["cash_expense"] == 0
                  and not movements and not transactions)
        if is_new:
            controls = [
                ft.Text(t(self.page, "dash_title"), size=24,
                        weight=ft.FontWeight.W_700),
                self._empty_state(),
            ]
            if self.msg_bar is not None:
                controls.append(self.msg_bar)
            return ft.Column(
                controls=controls,
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

        kpis = ft.ResponsiveRow(
            controls=[
                ft.Container(self._kpi_card(t(self.page, "kpi_stock_value"), fmt(data["stock_value"]), ft.Icons.INVENTORY, T.PRIMARY), col={"sm": 6, "lg": 4, "xl": 2}),
                ft.Container(self._kpi_card(t(self.page, "kpi_potential_profit"), fmt(data["potential_profit"]), ft.Icons.TRENDING_UP, T.SUCCESS), col={"sm": 6, "lg": 4, "xl": 2}),
                ft.Container(self._kpi_card(t(self.page, "kpi_cash_balance"), fmt(data["cash_balance"]), ft.Icons.ACCOUNT_BALANCE_WALLET, T.WARNING), col={"sm": 6, "lg": 4, "xl": 2}),
                ft.Container(self._kpi_card(t(self.page, "kpi_total_products"), str(data["product_count"]), ft.Icons.CATEGORY, T.PRIMARY), col={"sm": 6, "lg": 4, "xl": 2}),
                ft.Container(self._kpi_card(t(self.page, "kpi_low_stock"), str(data["low_stock_count"]), ft.Icons.WARNING_AMBER, T.LOW_STOCK), col={"sm": 6, "lg": 4, "xl": 2}),
                ft.Container(self._kpi_card(t(self.page, "kpi_credit_outstanding"), fmt(data["credit_outstanding"]), ft.Icons.CREDIT_CARD, T.ACCENT), col={"sm": 6, "lg": 4, "xl": 2}),
            ],
            spacing=12,
            run_spacing=12,
        )

        recent_movements = responsive.hscroll(
            self._movements_table(movements), self.page)
        recent_transactions = responsive.hscroll(
            self._transactions_table(transactions), self.page)

        controls = [
                ft.Text(t(self.page, "dash_title"), size=24, weight=ft.FontWeight.W_700),
                kpis,
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            self._table_card(t(self.page, "recent_movements"), recent_movements),
                            col={"sm": 12, "lg": 6}, padding=0,
                        ),
                        ft.Container(
                            self._table_card(t(self.page, "recent_transactions"), recent_transactions),
                            col={"sm": 12, "lg": 6}, padding=0,
                        ),
                    ],
                    spacing=12,
                    run_spacing=12,
                ),
            ]
        if self.msg_bar is not None:
            controls.append(self.msg_bar)
        return ft.Column(
            controls=controls,
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _empty_state(self):
        dark = (self.page.session.store.get("theme_mode") or "dark") == "dark"
        surface = T.SURFACE_DARK if dark else T.SURFACE_LIGHT
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.DASHBOARD_OUTLINED, size=56,
                            color="#888888"),
                    ft.Text(t(self.page, "empty_dashboard"), size=18,
                            weight=ft.FontWeight.W_700),
                    ft.Text(t(self.page, "empty_dashboard_hint"), size=13,
                            color="#888888", text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            padding=40,
            bgcolor=surface,
            border_radius=14,
        )

    def _table_card(self, title, table):
        dark = (self.page.session.store.get("theme_mode") or "dark") == "dark"
        surface = T.SURFACE_DARK if dark else T.SURFACE_LIGHT
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(title, size=16, weight=ft.FontWeight.W_600),
                    table,
                ],
                spacing=10,
            ),
            padding=16,
            bgcolor=surface,
            border_radius=14,
        )

    def _movements_table(self, rows):
        if not rows:
            return ft.Text(t(self.page, "no_data"), size=13)
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(t(self.page, "name"))),
                ft.DataColumn(ft.Text(t(self.page, "type"))),
                ft.DataColumn(ft.Text(t(self.page, "quantity"))),
                ft.DataColumn(ft.Text(t(self.page, "date"))),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(r["product_name"] or "", size=13)),
                        ft.DataCell(ft.Text(
                            t(self.page, "stock_in" if r["type"] == "in" else "stock_out"),
                            size=13,
                            color=T.SUCCESS if r["type"] == "in" else T.ERROR,
                            weight=ft.FontWeight.W_600,
                        )),
                        ft.DataCell(ft.Text(
                            f"+{r['quantity']:g}" if r["type"] == "in" else f"-{r['quantity']:g}",
                            size=13,
                            color=T.SUCCESS if r["type"] == "in" else T.ERROR,
                            font_family=T.NUMBER_FONT,
                        )),
                        ft.DataCell(ft.Text(r["date"] or "", size=12)),
                    ]
                )
                for r in rows
            ],
        )

    def _transactions_table(self, rows):
        if not rows:
            return ft.Text(t(self.page, "no_data"), size=13)
        cur = get_currency_code(self.page)
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(t(self.page, "type"))),
                ft.DataColumn(ft.Text(t(self.page, "amount"))),
                ft.DataColumn(ft.Text(t(self.page, "category"))),
                ft.DataColumn(ft.Text(t(self.page, "date"))),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(
                            t(self.page, "income" if r["type"] == "income" else "expense"),
                            size=13,
                            color=T.SUCCESS if r["type"] == "income" else T.ERROR,
                            weight=ft.FontWeight.W_600,
                        )),
                        ft.DataCell(ft.Text(
                            f"+{format_currency(r['amount'], cur)}"
                            if r["type"] == "income" else f"-{format_currency(r['amount'], cur)}",
                            size=13,
                            color=T.SUCCESS if r["type"] == "income" else T.ERROR,
                            font_family=T.NUMBER_FONT,
                        )),
                        ft.DataCell(ft.Text(tx_category_label(self.page, r["category"]), size=13)),
                        ft.DataCell(ft.Text(r["date"] or "", size=12)),
                    ]
                )
                for r in rows
            ],
        )