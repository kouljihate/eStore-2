import functools
import os

import flet as ft

from app import barcode as bc
from app import responsive
from app import theme as T
from app.activity import log_action
from app.currency import format_currency, get_currency_code
from app.database import (
    add_credit_note,
    add_customer,
    add_product,
    add_stock_movement,
    delete_product,
    get_customer,
    get_customers,
    get_product,
    get_product_by_barcode,
    get_products,
    get_stock_movements_by_product,
    record_sale,
    update_product,
)
from app.printing import print_stickers
from app.translations import t

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "assets",
)


class StockScreen:
    def __init__(self, page):
        self.page = page
        self.msg_bar = page.msg_bar
        self.uid = page.session.store.get("user_id")
        self.products = []
        self.filtered = []
        self.list_view = ft.Column(spacing=10)
        self.search_field = ft.TextField(
            hint_text=t(page, "search"),
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            dense=True,
            expand=True,
            on_change=lambda e: self._refresh(),
        )

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build(self):
        self._load()

        header = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(t(self.page, "products_title"),
                                size=22, weight=ft.FontWeight.W_700,
                                expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            tooltip=t(self.page, "clear"),
                            on_click=lambda e: self._clear_search(),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    controls=[
                        self.search_field,
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            icon_color=T.PRIMARY,
                            tooltip=t(self.page, "add_product"),
                            on_click=lambda e: self._open_product_dialog(None),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.PRINT,
                            icon_color=T.PRIMARY,
                            tooltip=t(self.page, "print_stickers"),
                            on_click=lambda e: self._open_print_dialog(),
                        ),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=8,
        )

        self._refresh(update=False)
        return ft.Column(
            controls=[header, self.list_view, self.msg_bar],
            spacing=12,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------
    def _load(self):
        self.products = get_products(self.uid)

    def _refresh(self, update=True):
        query = (self.search_field.value or "").strip().lower()
        if query:
            self.filtered = [
                p for p in self.products
                if query in (p["name"] or "").lower()
                or query in (p["category"] or "").lower()
                or query in (p["barcode"] or "").lower()
                or query in (p["supplier_name"] or "").lower()
            ]
        else:
            self.filtered = list(self.products)

        self.list_view.controls.clear()
        if not self.products:
            self.list_view.controls.append(self._empty_stock_state())
        elif not self.filtered:
            self.list_view.controls.append(
                ft.Container(
                    content=ft.Text(t(self.page, "no_products_found"),
                                    size=14, color="#888888"),
                    alignment=ft.Alignment.CENTER,
                    padding=30,
                )
            )
        else:
            for product in self.filtered:
                self.list_view.controls.append(self._product_card(product))
        if not update:
            return
        try:
            self.page.update()
        except Exception:
            pass

    def _empty_stock_state(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, size=56,
                            color="#888888"),
                    ft.Text(t(self.page, "no_stock_title"), size=18,
                            weight=ft.FontWeight.W_700),
                    ft.Text(t(self.page, "no_stock_hint"), size=13,
                            color="#888888",
                            text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            alignment=ft.Alignment.CENTER,
            padding=40,
        )

    def _clear_search(self):
        self.search_field.value = ""
        self._refresh()

    # ------------------------------------------------------------------
    # Product card
    # ------------------------------------------------------------------
    def _product_card(self, p):
        dark = (self.page.session.store.get("theme_mode") or "dark") == "dark"
        surface = T.SURFACE_DARK if dark else T.SURFACE_LIGHT
        cur = get_currency_code(self.page)
        low = self._is_low(p)
        qty_color = T.LOW_STOCK if low else (T.TEXT_DARK if dark else T.TEXT_LIGHT)

        actions = ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.EDIT, icon_color=T.PRIMARY,
                              tooltip=t(self.page, "edit"),
                              on_click=functools.partial(self._open_product_dialog, p)),
                ft.OutlinedButton(
                    content=t(self.page, "sell"), icon=ft.Icons.POINT_OF_SALE,
                    style=ft.ButtonStyle(
                        color=T.SUCCESS,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    ),
                    on_click=functools.partial(self._open_sell, p),
                ),
                ft.OutlinedButton(
                    content=t(self.page, "sell_credit"), icon=ft.Icons.CREDIT_SCORE,
                    style=ft.ButtonStyle(
                        color=T.WARNING,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    ),
                    on_click=functools.partial(self._open_credit_sell, p),
                ),
                ft.OutlinedButton(
                    content=t(self.page, "stock_in"), icon=ft.Icons.INBOX,
                    style=ft.ButtonStyle(
                        color=T.PRIMARY,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    ),
                    on_click=functools.partial(self._open_movement, p, "in"),
                ),
                ft.OutlinedButton(
                    content=t(self.page, "stock_out"), icon=ft.Icons.OUTBOX,
                    style=ft.ButtonStyle(
                        color=T.ERROR,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    ),
                    on_click=functools.partial(self._open_movement, p, "out"),
                ),
                ft.IconButton(icon=ft.Icons.HISTORY, icon_color=T.WARNING,
                              tooltip=t(self.page, "history"),
                              on_click=functools.partial(self._open_history, p)),
                ft.IconButton(icon=ft.Icons.DELETE, icon_color=T.ERROR,
                              tooltip=t(self.page, "delete"),
                              on_click=functools.partial(self._open_delete, p)),
            ],
            spacing=4,
            wrap=True,
        )

        info = []
        if p["category"]:
            info.append(p["category"])
        if p["packaging"]:
            info.append(p["packaging"])
        if p["barcode"]:
            info.append(f"{t(self.page, 'barcode')}: {p['barcode']}")

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(p["name"], size=16,
                                            weight=ft.FontWeight.W_700),
                                    ft.Text(" • ".join(info), size=12,
                                            color="#888888") if info else
                                    ft.Text("", size=1),
                                    ft.Text(
                                        p["supplier_name"] or "",
                                        size=12, color="#888888"),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(
                                            f"{p['quantity']:g}",
                                            size=20, weight=ft.FontWeight.W_700,
                                            color=qty_color,
                                            font_family=T.NUMBER_FONT),
                                        bgcolor=f"{qty_color}22",
                                        border_radius=8,
                                        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                                    ),
                                    ft.Text(format_currency(p["price"], cur),
                                            size=15, weight=ft.FontWeight.W_600,
                                            color=T.PRIMARY,
                                            font_family=T.NUMBER_FONT),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=4,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    actions,
                ],
                spacing=10,
            ),
            padding=14,
            bgcolor=surface,
            border_radius=12,
        )

    def _is_low(self, p):
        try:
            return float(p["quantity"] or 0) <= float(p["low_stock_qty"] or 0)
        except (TypeError, ValueError):
            return False

    # ------------------------------------------------------------------
    # Add/Edit Product dialog
    # ------------------------------------------------------------------
    def _open_product_dialog(self, p):
        editing = p is not None
        self._editing_id = p["id"] if editing else None
        pv = (lambda k: p[k] if p[k] is not None else "") if editing else (lambda k: "")

        def field(label, value="", icon=None, numeric=False, lines=1, suffix=None):
            kwargs = dict(
                label=label,
                value=str(value) if value is not None else "",
                border_radius=8,
                dense=True,
            )
            if icon:
                kwargs["prefix_icon"] = icon
            if numeric:
                kwargs["keyboard_type"] = ft.KeyboardType.NUMBER
            if suffix:
                kwargs["suffix_text"] = suffix
            return ft.TextField(**kwargs)

        self.f_name = field(t(self.page, "product_name"), pv("name"), ft.Icons.SHOP)
        self.f_qty = field(t(self.page, "stock_qty"), pv("quantity"), ft.Icons.NUMBERS, True)
        self.f_price = field(t(self.page, "selling_price"), pv("price"), ft.Icons.PRICE_CHANGE, True)
        self.f_buy = field(t(self.page, "buying_price"), pv("buying_price"), ft.Icons.DOWNLOADING, True)
        self.f_category = field(t(self.page, "product_category"), pv("category"), ft.Icons.CATEGORY)
        self.f_packaging = field(t(self.page, "packaging"), pv("packaging"), ft.Icons.INVENTORY_2)
        self.f_low = field(t(self.page, "low_stock_qty"), pv("low_stock_qty"), ft.Icons.WARNING_AMBER, True)
        self.f_description = field(t(self.page, "product_description"), pv("description"), ft.Icons.NOTES, lines=2)
        self.f_supplier = field(t(self.page, "supplier_name"), pv("supplier_name"), ft.Icons.BUSINESS)
        self.f_whatsapp = field(t(self.page, "supplier_whatsapp"), pv("supplier_whatsapp"), ft.Icons.CHAT)
        self.f_semail = field(t(self.page, "supplier_email"), pv("supplier_email"), ft.Icons.MAIL)
        self.f_barcode = field(t(self.page, "barcode"), pv("barcode"), ft.Icons.BARCODE_READER)

        self._barcode_preview = ft.Container(
            content=ft.Text(t(self.page, "barcode_preview"), size=12, color="#888888"),
            bgcolor="#FFFFFF",
            border_radius=8,
            padding=8,
            alignment=ft.Alignment.CENTER,
            visible=bool(self.f_barcode.value),
        )
        if self.f_barcode.value:
            img = bc.barcode_image(self.f_barcode.value, width=260, max_height=80)
            self._barcode_preview.content = img

        def on_generate(e):
            for _ in range(20):
                code = bc.generate_unique_code()
                if not get_product_by_barcode(code, self.uid):
                    break
            self.f_barcode.value = code
            self._barcode_preview.content = bc.barcode_image(
                code, width=260, max_height=80)
            self._barcode_preview.visible = True
            self.page.update()

        form = ft.Column(
            controls=[
                self.f_name,
                ft.Row(controls=[self.f_qty, self.f_low], spacing=8),
                ft.Row(controls=[self.f_price, self.f_buy], spacing=8),
                self.f_category,
                self.f_packaging,
                self.f_supplier,
                ft.Row(controls=[self.f_whatsapp, self.f_semail], spacing=8),
                self.f_description,
                self.f_barcode,
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            content=t(self.page, "generate_barcode"),
                            icon=ft.Icons.QR_CODE_2,
                            on_click=on_generate,
                        ),
                        self._barcode_preview,
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            width=responsive.dialog_width(self.page, 430),
        )

        self.product_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(t(self.page, "edit_product" if editing else "add_product")),
            content=form,
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(self.product_dialog)),
                ft.FilledButton(t(self.page, "save"),
                                on_click=lambda e: self._save_product()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(self.product_dialog)

    def _save_product(self):
        name = (self.f_name.value or "").strip()
        if not name:
            self.msg_bar.show_error(t(self.page, "required_field"))
            return
        try:
            qty = float((self.f_qty.value or "0").strip())
            price = float((self.f_price.value or "0").strip())
            buy = float((self.f_buy.value or "0").strip())
            low = float((self.f_low.value or "5").strip())
        except ValueError:
            self.msg_bar.show_error(t(self.page, "value_invalid"))
            return
        if qty < 0 or price < 0 or buy < 0 or low < 0:
            self.msg_bar.show_error(t(self.page, "value_invalid"))
            return
        if qty > 1e9 or price > 1e9 or buy > 1e9:
            self.msg_bar.show_error(t(self.page, "value_invalid"))
            return

        barcode = (self.f_barcode.value or "").strip()
        if barcode:
            existing = get_product_by_barcode(barcode, self.uid)
            if existing and existing["id"] != self._editing_id:
                self.msg_bar.show_error(t(self.page, "value_invalid"))
                return

        params = dict(
            name=name,
            quantity=qty,
            price=price,
            buying_price=buy,
            category=(self.f_category.value or "").strip(),
            packaging=(self.f_packaging.value or "").strip(),
            description=(self.f_description.value or "").strip(),
            low_stock_qty=low,
            supplier_name=(self.f_supplier.value or "").strip(),
            supplier_whatsapp=(self.f_whatsapp.value or "").strip(),
            supplier_email=(self.f_semail.value or "").strip(),
            barcode=barcode,
        )
        if self._editing_id is None:
            pid = add_product(self.uid, **params)
            log_action(self.page, "product_add", f"name={name} id={pid}")
            self.msg_bar.show_success(t(self.page, "product_added"))
        else:
            update_product(self._editing_id, user_id=self.uid, **params)
            log_action(self.page, "product_edit", f"id={self._editing_id} name={name}")
            self.msg_bar.show_success(t(self.page, "product_updated"))
        self._close(self.product_dialog)
        self._load()
        self._refresh()

    # ------------------------------------------------------------------
    # Bulk add dialog
    # ------------------------------------------------------------------
    BULK_ROWS = 5

    def _open_bulk_dialog(self):
        self._bulk_rows = []
        rows = []
        for _ in range(self.BULK_ROWS):
            f_name = ft.TextField(
                label=t(self.page, "product_name"), dense=True,
                border_radius=8, expand=True,
            )
            f_qty = ft.TextField(
                label=t(self.page, "item_qty"), value="0",
                keyboard_type=ft.KeyboardType.NUMBER, dense=True,
                border_radius=8, width=90,
            )
            f_price = ft.TextField(
                label=t(self.page, "unit_price"), value="0",
                keyboard_type=ft.KeyboardType.NUMBER, dense=True,
                border_radius=8, width=110,
            )
            self._bulk_rows.append((f_name, f_qty, f_price))
            rows.append(ft.Row(controls=[f_name, f_qty, f_price], spacing=8))

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(t(self.page, "add_bulk_products")),
            content=ft.Column(
                controls=rows,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                width=responsive.dialog_width(self.page, 430),
            ),
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(dialog)),
                ft.FilledButton(t(self.page, "save"),
                                on_click=lambda e: self._save_bulk()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._bulk_dialog = dialog
        self.page.show_dialog(dialog)

    def _save_bulk(self):
        parsed = []
        for f_name, f_qty, f_price in self._bulk_rows:
            name = (f_name.value or "").strip()
            if not name:
                continue
            try:
                qty = float((f_qty.value or "0").strip())
                price = float((f_price.value or "0").strip())
            except ValueError:
                self.msg_bar.show_error(t(self.page, "value_invalid"))
                return
            if qty < 0 or price < 0:
                self.msg_bar.show_error(t(self.page, "value_invalid"))
                return
            parsed.append((name, qty, price))
        if not parsed:
            self.msg_bar.show_error(t(self.page, "item_required"))
            return
        for name, qty, price in parsed:
            add_product(self.uid, name, quantity=qty, price=price)
        log_action(self.page, "product_bulk_add", f"count={len(parsed)}")
        self.msg_bar.show_success(
            f"{len(parsed)} — {t(self.page, 'bulk_added')}")
        self._close(self._bulk_dialog)
        self._load()
        self._refresh()

    # ------------------------------------------------------------------
    # Delete dialog
    # ------------------------------------------------------------------
    def _open_delete(self, p):
        self._delete_id = p["id"]
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(t(self.page, "delete")),
            content=ft.Text(t(self.page, "delete_confirm")),
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(dialog)),
                ft.FilledButton(t(self.page, "delete"),
                                style=ft.ButtonStyle(bgcolor=T.ERROR),
                                on_click=lambda e: self._do_delete()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._delete_dialog = dialog
        self.page.show_dialog(dialog)

    def _do_delete(self):
        log_action(self.page, "product_delete", f"id={self._delete_id}")
        delete_product(self._delete_id, user_id=self.uid)
        self.msg_bar.show_success(t(self.page, "product_deleted"))
        self._close(self._delete_dialog)
        self._load()
        self._refresh()

    # ------------------------------------------------------------------
    # Sell dialog
    # ------------------------------------------------------------------
    def _open_sell(self, p):
        self._sell_product = p
        self.f_sell_qty = ft.TextField(
            label=t(self.page, "sell_quantity"),
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            border_radius=8,
            autofocus=True,
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{t(self.page, 'sell')} — {p['name']}"),
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"{t(self.page, 'stock_qty')}: {p['quantity']:g}  •  "
                        f"{format_currency(p['price'], get_currency_code(self.page))}",
                        size=13,
                        font_family=T.NUMBER_FONT,
                    ),
                    self.f_sell_qty,
                ],
                spacing=10,
                width=responsive.dialog_width(self.page, 300),
            ),
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(dialog)),
                ft.FilledButton(t(self.page, "sell"),
                                on_click=lambda e: self._do_sell()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._sell_dialog = dialog
        self.page.show_dialog(dialog)

    def _do_sell(self):
        try:
            qty = float((self.f_sell_qty.value or "0").strip())
        except ValueError:
            qty = 0
        if qty <= 0:
            self.msg_bar.show_error(t(self.page, "invalid_quantity"))
            return
        p = self._sell_product
        fresh = get_product(p["id"], user_id=self.uid)
        if not fresh:
            self.msg_bar.show_error(t(self.page, "generic_error"))
            self._close(self._sell_dialog)
            return
        if qty > fresh["quantity"]:
            self.msg_bar.show_error(t(self.page, "insufficient_stock"))
            return
        if record_sale(self.uid, p["id"], qty, note="sale"):
            log_action(self.page, "sale", f"product={p['id']} qty={qty:g}")
            self.msg_bar.show_success(t(self.page, "sale_success"))
        else:
            log_action(self.page, "sale_failed", f"product={p['id']} qty={qty:g}")
            self.msg_bar.show_error(t(self.page, "generic_error"))
        self._close(self._sell_dialog)
        self._load()
        self._refresh()

    # ------------------------------------------------------------------
    # Sell on credit
    # ------------------------------------------------------------------
    def _open_credit_sell(self, p):
        self._credit_product = p
        customers = get_customers(self.uid)

        self._seg_new = ft.RadioGroup(
            content=ft.Row(
                controls=[
                    ft.Radio(value="existing", label=t(self.page, "existing_customer")),
                    ft.Radio(value="new", label=t(self.page, "new_customer")),
                ]
            ),
            value="existing",
            on_change=lambda e: self._toggle_customer(),
        )
        self.customer_dropdown = ft.Dropdown(
            label=t(self.page, "select_customer"),
            options=[ft.dropdown.Option(str(c["id"]), c["name"]) for c in customers],
            dense=True,
            border_radius=8,
            width=300,
        )
        self.f_cname = ft.TextField(
            label=t(self.page, "customer_name"), dense=True, border_radius=8,
            visible=False,
        )
        self.f_cphone = ft.TextField(
            label=t(self.page, "customer_phone"), dense=True, border_radius=8,
            visible=False,
        )
        self.f_credit_qty = ft.TextField(
            label=t(self.page, "item_qty"), value="1",
            keyboard_type=ft.KeyboardType.NUMBER, dense=True, border_radius=8,
            width=130,
        )
        self.f_credit_price = ft.TextField(
            label=t(self.page, "unit_price"),
            value=str(p["price"]) if p["price"] else "0",
            keyboard_type=ft.KeyboardType.NUMBER, dense=True, border_radius=8,
            width=130,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{t(self.page, 'sell_credit')} — {p['name']}"),
            content=ft.Column(
                controls=[
                    self._seg_new,
                    self.customer_dropdown,
                    self.f_cname,
                    self.f_cphone,
                    ft.Row(controls=[self.f_credit_qty, self.f_credit_price],
                           spacing=8),
                ],
                spacing=10,
                width=responsive.dialog_width(self.page, 330),
            ),
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(dialog)),
                ft.FilledButton(t(self.page, "save"),
                                on_click=lambda e: self._do_credit_sell()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._credit_dialog = dialog
        self._toggle_customer()
        self.page.show_dialog(dialog)

    def _toggle_customer(self):
        is_new = (self._seg_new.value == "new")
        self.customer_dropdown.visible = not is_new
        self.f_cname.visible = is_new
        self.f_cphone.visible = is_new
        self.page.update()

    def _do_credit_sell(self):
        p = self._credit_product
        try:
            qty = float((self.f_credit_qty.value or "0").strip())
            unit_price = float((self.f_credit_price.value or "0").strip())
        except ValueError:
            qty = 0
            unit_price = 0
        if qty <= 0 or unit_price < 0:
            self.msg_bar.show_error(t(self.page, "invalid_quantity"))
            return

        if self._seg_new.value == "new":
            cname = (self.f_cname.value or "").strip()
            if not cname:
                self.msg_bar.show_error(t(self.page, "customer_required"))
                return
            customer_id = add_customer(self.uid, cname, (self.f_cphone.value or "").strip())
        else:
            try:
                customer_id = int(self.customer_dropdown.value)
            except (TypeError, ValueError):
                self.msg_bar.show_error(t(self.page, "customer_required"))
                return
            if not get_customer(customer_id, user_id=self.uid):
                self.msg_bar.show_error(t(self.page, "customer_required"))
                return

        items = [(p["id"], p["name"], qty, unit_price, round(qty * unit_price, 2))]
        cn_id, ok, err = add_credit_note(self.uid, customer_id, items)
        if ok:
            log_action(self.page, "credit_sell",
                       f"product={p['id']} qty={qty:g} customer={customer_id} note={cn_id}")
            self.msg_bar.show_success(t(self.page, "note_created"))
        else:
            log_action(self.page, "credit_sell_failed",
                       f"product={p['id']} qty={qty:g} err={err}")
            self.msg_bar.show_error(
                t(self.page, "insufficient_stock") if err == "stock"
                else t(self.page, "generic_error"))
        self._close(self._credit_dialog)
        self._load()
        self._refresh()

    # ------------------------------------------------------------------
    # Stock movement dialog
    # ------------------------------------------------------------------
    def _open_movement(self, p, mtype):
        self._mv_product = p
        self._mv_type = mtype
        self.f_mv_qty = ft.TextField(
            label=t(self.page, "quantity"),
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            border_radius=8,
            autofocus=True,
        )
        self.f_mv_note = ft.TextField(
            label=t(self.page, "movement_note"),
            dense=True,
            border_radius=8,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"{t(self.page, 'add_stock_in' if mtype == 'in' else 'add_stock_out')}"
                f" — {p['name']}"),
            content=ft.Column(
                controls=[
                    ft.Text(f"{t(self.page, 'stock_qty')}: {p['quantity']:g}", size=13,
                            font_family=T.NUMBER_FONT),
                    self.f_mv_qty,
                    self.f_mv_note,
                ],
                spacing=10,
                width=responsive.dialog_width(self.page, 300),
            ),
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(dialog)),
                ft.FilledButton(t(self.page, "save"),
                                on_click=lambda e: self._do_movement()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._mv_dialog = dialog
        self.page.show_dialog(dialog)

    def _do_movement(self):
        try:
            qty = float((self.f_mv_qty.value or "0").strip())
        except ValueError:
            qty = 0
        if qty <= 0:
            self.msg_bar.show_error(t(self.page, "invalid_quantity"))
            return
        note = (self.f_mv_note.value or "").strip() or (
            self._mv_type)
        ok = add_stock_movement(
            self._mv_product["id"], self.uid, self._mv_type, qty, note)
        if ok:
            log_action(self.page, "stock_movement",
                       f"product={self._mv_product['id']} type={self._mv_type} qty={qty:g}")
            self.msg_bar.show_success(t(
                self.page, "stock_in_success" if self._mv_type == "in"
                else "stock_out_success"))
        else:
            self.msg_bar.show_error(t(self.page, "movement_too_many"))
        self._close(self._mv_dialog)
        self._load()
        self._refresh()

    # ------------------------------------------------------------------
    # Movement history dialog
    # ------------------------------------------------------------------
    def _open_history(self, p):
        rows = get_stock_movements_by_product(self.uid, p["id"], limit=50)
        if rows:
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text(t(self.page, "type"))),
                    ft.DataColumn(ft.Text(t(self.page, "quantity"))),
                    ft.DataColumn(ft.Text(t(self.page, "note"))),
                    ft.DataColumn(ft.Text(t(self.page, "date"))),
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(
                                t(self.page, "stock_in" if r["type"] == "in"
                                  else "stock_out"),
                                size=13,
                                color=T.SUCCESS if r["type"] == "in" else T.ERROR)),
                            ft.DataCell(ft.Text(
                                f"+{r['quantity']:g}" if r["type"] == "in"
                                else f"-{r['quantity']:g}",
                                size=13,
                                color=T.SUCCESS if r["type"] == "in" else T.ERROR,
                                font_family=T.NUMBER_FONT)),
                            ft.DataCell(ft.Text(r["note"] or "", size=12)),
                            ft.DataCell(ft.Text(r["date"] or "", size=11)),
                        ]
                    )
                    for r in rows
                ],
            )
        else:
            table = ft.Text(t(self.page, "no_data"), size=13)

        dialog = ft.AlertDialog(
            title=ft.Text(f"{t(self.page, 'movement_history_title')} — {p['name']}"),
            content=ft.Container(
                content=ft.Column(
                    controls=[responsive.hscroll(table, self.page)],
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=responsive.dialog_width(self.page, 550),
            ),
            actions=[
                ft.TextButton(t(self.page, "close"),
                              on_click=lambda e: self._close(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    # ------------------------------------------------------------------
    # Print stickers dialog
    # ------------------------------------------------------------------
    def _open_print_dialog(self):
        self._print_checks = {}
        checks = []
        for p in self.products:
            cb = ft.Checkbox(
                label=p["name"], value=False,
                data=p["id"],
            )
            self._print_checks[p["id"]] = cb
            checks.append(cb)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(t(self.page, "print_select")),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.TextButton(t(self.page, "all"),
                                              on_click=lambda e: self._set_all(True)),
                                ft.TextButton(t(self.page, "clear"),
                                              on_click=lambda e: self._set_all(False)),
                            ],
                            spacing=6,
                        ),
                        ft.Column(controls=checks, scroll=ft.ScrollMode.AUTO, spacing=2),
                    ],
                    spacing=8,
                    width=responsive.dialog_width(self.page, 380),
                ),
            ),
            actions=[
                ft.TextButton(t(self.page, "cancel"),
                              on_click=lambda e: self._close(dialog)),
                ft.FilledButton(t(self.page, "print_stickers"),
                                icon=ft.Icons.PRINT,
                                on_click=lambda e: self._do_print(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def _set_all(self, value):
        for cb in self._print_checks.values():
            cb.value = value
        self.page.update()

    def _do_print(self, dialog):
        selected = [
            get_product(pid, user_id=self.uid) for pid, cb in self._print_checks.items() if cb.value
        ]
        selected = [p for p in selected if p]
        if not selected:
            self.msg_bar.show_warning(t(self.page, "print_select"))
            self._close(dialog)
            return
        print_stickers(
            selected,
            currency_symbol=self.page.session.store.get("currency") or "MAD",
        )
        log_action(self.page, "print_stickers", f"count={len(selected)}")
        self.msg_bar.show_success(t(self.page, "stickers_printed"))
        self._close(dialog)

    # ------------------------------------------------------------------
    def _close(self, dialog):
        try:
            self.page.pop_dialog()
        except Exception:
            dialog.open = False
            self.page.update()