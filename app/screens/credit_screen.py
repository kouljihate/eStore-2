import functools

import flet as ft

from app import responsive
from app import theme as T
from app.activity import log_action
from app.currency import format_currency, get_currency_code
from app.database import (
    add_credit_note,
    add_credit_payment,
    add_customer,
    get_credit_note,
    get_credit_note_items,
    get_credit_payments,
    get_credit_notes,
    get_credit_summary,
    get_customer,
    get_customers,
    get_product,
    get_products,
)
from app.translations import t

FILTERS = {"all": None, "open": "open", "closed": "closed"}


class CreditScreen:
    def __init__(self, page, on_rebuild=None):
        self.page = page
        self.on_rebuild = on_rebuild
        self.msg_bar = page.msg_bar
        self.uid = page.session.store.get("user_id")
        self.filter = "all"
        self.items = []

    def _surface(self):
        dark = (self.page.session.store.get("theme_mode") or "dark") == "dark"
        return T.SURFACE_DARK if dark else T.SURFACE_LIGHT

    def _badge(self, status):
        return ft.Container(
            content=ft.Text(
                t(self.page, "status_open" if status == "open" else "status_closed"),
                size=12,
                weight=ft.FontWeight.W_600,
                color=T.SUCCESS if status == "closed" else T.WARNING,
            ),
            bgcolor=f"{T.SUCCESS if status == 'closed' else T.WARNING}22",
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        )

    def build(self):
        cur = get_currency_code(self.page)
        summary = get_credit_summary(self.uid)
        notes = get_credit_notes(self.uid, status=FILTERS[self.filter])

        summary_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(t(self.page, "outstanding"), size=13,
                                    color="#888888"),
                            ft.Text(
                                format_currency(summary["total_outstanding"], cur),
                                size=28, weight=ft.FontWeight.W_700,
                                color=T.WARNING,
                                font_family=T.NUMBER_FONT),
                        ],
                        expand=True,
                        spacing=2,
                    ),
                    ft.VerticalDivider(width=1),
                    ft.Column(
                        controls=[
                            ft.Text(t(self.page, "open_count"), size=13,
                                    color="#888888"),
                            ft.Text(str(summary["open_count"]),
                                    size=28, weight=ft.FontWeight.W_700,
                                    color=T.ACCENT,
                                    font_family=T.NUMBER_FONT),
                        ],
                        expand=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    ft.VerticalDivider(width=1),
                    ft.Column(
                        controls=[
                            ft.Text(t(self.page, "total"), size=13, color="#888888"),
                            ft.Text(
                                format_currency(
                                    sum(n["total_amount"] for n in notes), cur),
                                size=20, weight=ft.FontWeight.W_700,
                                color=T.TEXT_DARK if (self.page.session.store.get("theme_mode") or "dark") == "dark" else T.TEXT_LIGHT,
                                font_family=T.NUMBER_FONT),
                        ],
                        expand=True,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=2,
                    ),
                ],
                spacing=14,
            ),
            padding=18,
            bgcolor=self._surface(),
            border_radius=14,
        )

        filter_bar = ft.SegmentedButton(
            segments=[
                ft.Segment(value="all",
                           label=ft.Text(t(self.page, "all"), size=12)),
                ft.Segment(value="open",
                           label=ft.Text(t(self.page, "status_open"), size=12)),
                ft.Segment(value="closed",
                           label=ft.Text(t(self.page, "status_closed"), size=12)),
            ],
            selected=[self.filter],
            show_selected_icon=False,
            padding=4,
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            ),
            on_change=lambda e: self._set_filter(e),
        )

        note_cards = self._note_cards(notes)

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(t(self.page, "credit_title"), size=22,
                                weight=ft.FontWeight.W_700),
                        ft.Container(expand=True),
                        ft.FilledButton(
                            content=t(self.page, "add_credit_note"),
                            icon=ft.Icons.NOTE_ADD,
                            on_click=lambda e: self._open_add_note()),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                summary_card,
                filter_bar,
                *note_cards,
                self.msg_bar,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _set_filter(self, e):
        self.filter = e.control.selected[0] if e.control.selected else "all"
        if self.on_rebuild:
            self.on_rebuild()

    def _note_card(self, note):
        cur = get_currency_code(self.page)
        remaining = note["total_amount"] - note["paid_amount"]
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(note["customer_name"], size=16,
                                            weight=ft.FontWeight.W_700),
                                    self._badge(note["status"]),
                                ],
                                spacing=8,
                            ),
                            ft.Text(
                                f"{t(self.page, 'total')}: "
                                f"{format_currency(note['total_amount'], cur)}   •   "
                                f"{t(self.page, 'paid')}: "
                                f"{format_currency(note['paid_amount'], cur)}",
                                size=13,
                                font_family=T.NUMBER_FONT,
                            ),
                            ft.Text(
                                f"{t(self.page, 'remaining')}: "
                                f"{format_currency(remaining, cur)}   •   "
                                f"{note['created_at']}",
                                size=12,
                                color=T.WARNING if remaining > 0 else T.SUCCESS,
                                weight=ft.FontWeight.W_600,
                                font_family=T.NUMBER_FONT,
                            ),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_FULL,
                        icon_color=T.PRIMARY,
                        tooltip=t(self.page, "close"),
                        on_click=functools.partial(self._open_detail, note["id"]),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=14,
            bgcolor=self._surface(),
            border_radius=12,
        )

    def _note_cards(self, notes):
        if not notes:
            return [ft.Container(
                content=ft.Text(t(self.page, "no_credit_notes"), size=14,
                                color="#888888"),
                alignment=ft.Alignment.CENTER,
                padding=30,
            )]
        return [self._note_card(n) for n in notes]

    # ------------------------------------------------------------------
    # Detail dialog
    # ------------------------------------------------------------------
    def _open_detail(self, note_id):
        note = get_credit_note(note_id, user_id=self.uid)
        if not note:
            self.msg_bar.show_error(t(self.page, "generic_error"))
            return
        cur = get_currency_code(self.page)
        items = get_credit_note_items(note_id, user_id=self.uid)
        payments = get_credit_payments(note_id, user_id=self.uid)

        items_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(t(self.page, "name"))),
                ft.DataColumn(ft.Text(t(self.page, "quantity"))),
                ft.DataColumn(ft.Text(t(self.page, "unit_price"))),
                ft.DataColumn(ft.Text(t(self.page, "total"))),
            ],
            rows=[
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(i["product_name"], size=13)),
                    ft.DataCell(ft.Text(f"{i['quantity']:g}", size=13,
                                        font_family=T.NUMBER_FONT)),
                    ft.DataCell(ft.Text(format_currency(i["unit_price"], cur), size=13,
                                        font_family=T.NUMBER_FONT)),
                    ft.DataCell(ft.Text(format_currency(i["total_price"], cur), size=13,
                                        font_family=T.NUMBER_FONT)),
                ])
                for i in items
            ],
        )

        if payments:
            pay_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text(t(self.page, "amount"))),
                    ft.DataColumn(ft.Text(t(self.page, "note"))),
                    ft.DataColumn(ft.Text(t(self.page, "date"))),
                ],
                rows=[
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(format_currency(p["amount"], cur), size=13,
                                            color=T.SUCCESS,
                                            font_family=T.NUMBER_FONT)),
                        ft.DataCell(ft.Text(p["note"] or "", size=12)),
                        ft.DataCell(ft.Text(p["date"] or "", size=11)),
                    ])
                    for p in payments
                ],
            )
        else:
            pay_table = ft.Text(t(self.page, "no_data"), size=13)

        remaining = note["total_amount"] - note["paid_amount"]
        actions = [
            ft.TextButton(t(self.page, "close"),
                          on_click=lambda e: self._close(dialog)),
        ]
        if note["status"] == "open":
            actions.insert(0, ft.FilledButton(
                t(self.page, "add_payment"),
                icon=ft.Icons.PAYMENTS,
                on_click=lambda e: self._open_payment(note, dialog)),
            )

        dialog = ft.AlertDialog(
            title=ft.Text(f"{t(self.page, 'credit_note')} #{note['id']} — "
                          f"{note['customer_name']}"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"{t(self.page, 'remaining')}: "
                            f"{format_currency(remaining, cur)}",
                            size=15, weight=ft.FontWeight.W_700,
                            color=T.WARNING if remaining > 0 else T.SUCCESS,
                            font_family=T.NUMBER_FONT),
                        ft.Text(t(self.page, "items"), size=14,
                                weight=ft.FontWeight.W_600),
                        responsive.hscroll(items_table, self.page),
                        ft.Text(t(self.page, "payment"), size=14,
                                weight=ft.FontWeight.W_600),
                        responsive.hscroll(pay_table, self.page),
                    ],
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    width=responsive.dialog_width(self.page, 560),
                ),
            ),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    # ------------------------------------------------------------------
    # Add credit note dialog
    # ------------------------------------------------------------------
    def _open_add_note(self):
        customers = get_customers(self.uid)
        products = get_products(self.uid)
        self.items = []

        self._seg_customer = ft.RadioGroup(
            content=ft.Row(
                controls=[
                    ft.Radio(value="existing",
                             label=t(self.page, "existing_customer")),
                    ft.Radio(value="new", label=t(self.page, "new_customer")),
                ]
            ),
            value="existing",
            on_change=lambda e: self._toggle_customer_fields(),
        )
        self.customer_dd = ft.Dropdown(
            label=t(self.page, "select_customer"),
            options=[ft.dropdown.Option(str(c["id"]), c["name"])
                     for c in customers],
            dense=True, border_radius=8,
        )
        self.f_cname = ft.TextField(
            label=t(self.page, "customer_name"), dense=True, border_radius=8,
            visible=False)
        self.f_cphone = ft.TextField(
            label=t(self.page, "customer_phone"), dense=True, border_radius=8,
            visible=False)

        self.product_dd = ft.Dropdown(
            label=t(self.page, "select_product"),
            options=[ft.dropdown.Option(str(p["id"]), p["name"])
                     for p in products],
            dense=True, border_radius=8,
            on_select=lambda e: self._autofill_price(products),
        )
        self.f_qty = ft.TextField(
            label=t(self.page, "item_qty"), value="1",
            keyboard_type=ft.KeyboardType.NUMBER, dense=True, border_radius=8,
            width=110)
        self.f_unit_price = ft.TextField(
            label=t(self.page, "unit_price"), value="0",
            keyboard_type=ft.KeyboardType.NUMBER, dense=True, border_radius=8,
            width=110)
        self.items_list = ft.Column(spacing=4)

        add_item_row = ft.Row(
            controls=[
                self.product_dd,
                self.f_qty,
                self.f_unit_price,
                ft.FilledButton(
                    t(self.page, "add_item"),
                    icon=ft.Icons.ADD,
                    on_click=lambda e: self._add_item(products)),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(t(self.page, "add_credit_note")),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        self._seg_customer,
                        self.customer_dd,
                        self.f_cname,
                        self.f_cphone,
                        add_item_row,
                        self.items_list,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    width=responsive.dialog_width(self.page, 560),
                ),
            ),
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(dialog)),
                ft.FilledButton(t(self.page, "save_credit_note"),
                                on_click=lambda e: self._save_note(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._add_note_dialog = dialog
        self._toggle_customer_fields()
        self.page.show_dialog(dialog)

    def _toggle_customer_fields(self):
        is_new = (self._seg_customer.value == "new")
        self.customer_dd.visible = not is_new
        self.f_cname.visible = is_new
        self.f_cphone.visible = is_new
        self.page.update()

    def _autofill_price(self, products):
        try:
            pid = int(self.product_dd.value)
        except (TypeError, ValueError):
            return
        for p in products:
            if p["id"] == pid:
                self.f_unit_price.value = str(p["price"])
                self.page.update()
                return

    def _add_item(self, products):
        try:
            pid = int(self.product_dd.value)
        except (TypeError, ValueError):
            self.msg_bar.show_error(t(self.page, "select_product"))
            return
        try:
            qty = float((self.f_qty.value or "0").strip())
            price = float((self.f_unit_price.value or "0").strip())
        except ValueError:
            qty = 0
            price = 0
        if qty <= 0:
            self.msg_bar.show_error(t(self.page, "invalid_quantity"))
            return
        if price < 0:
            self.msg_bar.show_error(t(self.page, "value_invalid"))
            return
        fresh = get_product(pid, user_id=self.uid)
        if not fresh:
            return
        already = sum(i["qty"] for i in self.items if i["product_id"] == pid)
        if qty + already > fresh["quantity"]:
            self.msg_bar.show_error(t(self.page, "insufficient_stock"))
            return
        self.items.append({
            "product_id": pid,
            "name": fresh["name"],
            "qty": qty,
            "unit_price": price,
            "total_price": round(qty * price, 2),
        })
        self.items_list.controls.append(self._item_row(len(self.items) - 1))
        self._reset_item_fields()
        self.page.update()

    def _item_row(self, index):
        item = self.items[index]
        cur = get_currency_code(self.page)
        return ft.Row(
            controls=[
                ft.Text(item["name"], size=13, expand=True),
                ft.Text(f"{item['qty']:g} × {format_currency(item['unit_price'], cur)}",
                        size=13, font_family=T.NUMBER_FONT),
                ft.Text(format_currency(item["total_price"], cur), size=13,
                        weight=ft.FontWeight.W_600,
                        font_family=T.NUMBER_FONT),
                ft.IconButton(
                    icon=ft.Icons.REMOVE_CIRCLE, icon_color=T.ERROR,
                    tooltip=t(self.page, "delete"),
                    on_click=lambda e, pid=item["product_id"], q=item["qty"],
                    up=item["unit_price"]: self._remove_item_by_value(pid, q, up)),
            ],
            spacing=6,
        )

    def _remove_item(self, index):
        try:
            del self.items[index]
        except IndexError:
            return
        self._rebuild_items_list()

    def _remove_item_by_value(self, product_id, qty, unit_price):
        for i, it in enumerate(self.items):
            if (it["product_id"] == product_id and it["qty"] == qty
                    and it["unit_price"] == unit_price):
                del self.items[i]
                break
        self._rebuild_items_list()

    def _rebuild_items_list(self):
        self.items_list.controls.clear()
        for idx in range(len(self.items)):
            self.items_list.controls.append(self._item_row(idx))
        self.page.update()

    def _reset_item_fields(self):
        self.product_dd.value = None
        self.f_qty.value = "1"
        self.f_unit_price.value = "0"

    def _resolve_customer(self):
        if self._seg_customer.value == "new":
            cname = (self.f_cname.value or "").strip()
            if not cname:
                return None, t(self.page, "customer_required")
            return add_customer(self.uid, cname, (self.f_cphone.value or "").strip()), ""
        try:
            cid = int(self.customer_dd.value)
        except (TypeError, ValueError):
            return None, t(self.page, "customer_required")
        if not get_customer(cid, user_id=self.uid):
            return None, t(self.page, "customer_required")
        return cid, ""

    def _save_note(self, dialog):
        if not self.items:
            self.msg_bar.show_error(t(self.page, "item_required"))
            return
        customer_id, err = self._resolve_customer()
        if customer_id is None:
            self.msg_bar.show_error(err)
            return
        items = [(i["product_id"], i["name"], i["qty"], i["unit_price"],
                  i["total_price"]) for i in self.items]
        cn_id, ok, err_code = add_credit_note(self.uid, customer_id, items)
        if ok:
            log_action(self.page, "credit_note_add",
                       f"note={cn_id} customer={customer_id} items={len(items)}")
            self.msg_bar.show_success(t(self.page, "note_created"))
        else:
            log_action(self.page, "credit_note_failed",
                       f"customer={customer_id} err={err_code}")
            self.msg_bar.show_error(
                t(self.page, "insufficient_stock") if err_code == "stock"
                else t(self.page, "generic_error"))
        self._close(dialog)
        if self.on_rebuild:
            self.on_rebuild()

    # ------------------------------------------------------------------
    # Payment dialog
    # ------------------------------------------------------------------
    def _open_payment(self, note, parent_dialog):
        cur = get_currency_code(self.page)
        remaining = note["total_amount"] - note["paid_amount"]
        self.pay_amount = ft.TextField(
            label=t(self.page, "payment_amount"),
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            border_radius=8,
            autofocus=True,
        )
        self.pay_note = ft.TextField(
            label=t(self.page, "payment_note"),
            dense=True,
            border_radius=8,
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{t(self.page, 'add_payment')} — "
                          f"{t(self.page, 'credit_note')} #{note['id']}"),
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"{t(self.page, 'remaining')}: "
                        f"{format_currency(remaining, cur)}",
                        size=15, weight=ft.FontWeight.W_700, color=T.WARNING,
                        font_family=T.NUMBER_FONT),
                    self.pay_amount,
                    self.pay_note,
                ],
                spacing=10,
                width=responsive.dialog_width(self.page, 300),
            ),
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(dialog)),
                ft.FilledButton(t(self.page, "save"),
                                on_click=lambda e:
                                self._do_payment(note, dialog, parent_dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def _do_payment(self, note, dialog, parent_dialog):
        try:
            amount = float((self.pay_amount.value or "0").strip())
        except ValueError:
            amount = 0
        if amount <= 0:
            self.msg_bar.show_error(t(self.page, "invalid_amount"))
            return
        fresh = get_credit_note(note["id"], user_id=self.uid)
        if not fresh:
            self.msg_bar.show_error(t(self.page, "generic_error"))
            self._close(dialog)
            return
        remaining = fresh["total_amount"] - fresh["paid_amount"]
        if amount > remaining + 0.001:
            self.msg_bar.show_error(t(self.page, "payment_exceeds"))
            return
        p_id, ok, _ = add_credit_payment(note["id"], amount,
                                         (self.pay_note.value or ""),
                                         user_id=self.uid)
        if not ok:
            log_action(self.page, "credit_payment_failed",
                       f"note={note['id']} amount={amount:g}")
            self.msg_bar.show_error(t(self.page, "generic_error"))
            self._close(dialog)
            return
        log_action(self.page, "credit_payment",
                   f"note={note['id']} amount={amount:g} pay={p_id}")
        new_remaining = remaining - amount
        if new_remaining < 0.001:
            self.msg_bar.show_success(t(self.page, "note_closed"))
        else:
            self.msg_bar.show_success(t(self.page, "payment_added"))
        self._close(dialog)
        self._close(parent_dialog)
        if self.on_rebuild:
            self.on_rebuild()

    def _close(self, dialog):
        try:
            self.page.pop_dialog()
        except Exception:
            dialog.open = False
            self.page.update()