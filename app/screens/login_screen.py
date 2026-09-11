import os
import re

import flet as ft

from app import theme as T
from app.activity import log_action
from app.database import authenticate_user, create_user, user_count
from app.responsive import viewport_width
from app.translations import t

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "assets", "eshop_icon.png",
)


class LoginScreen:
    def __init__(self, page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success
        self.is_register = user_count() == 0
        self.msg_bar = page.msg_bar

        self.name_field = ft.TextField(
            label=t(page, "full_name"),
            prefix_icon=ft.Icons.PERSON,
            border_radius=10,
            visible=self.is_register,
        )
        self.email_field = ft.TextField(
            label=t(page, "email"),
            prefix_icon=ft.Icons.EMAIL,
            keyboard_type=ft.KeyboardType.EMAIL,
            border_radius=10,
        )
        self.password_field = ft.TextField(
            label=t(page, "password"),
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=10,
            on_submit=self._handle_action,
        )
        self.action_button = ft.FilledButton(
            content=t(page, "register" if self.is_register else "login"),
            icon=ft.Icons.LOGIN if not self.is_register else ft.Icons.APP_REGISTRATION,
            on_click=self._handle_action,
            width=220,
            height=44,
        )
        self.subtitle = ft.Text(
            t(page, "first_run_welcome") if self.is_register else t(page, "login_title"),
            text_align=ft.TextAlign.CENTER,
            size=14,
        )

    def build(self):
        logo = None
        if os.path.exists(ICON_PATH):
            logo = ft.Image(src=ICON_PATH, width=110, height=110)

        heading = ft.Text(
            t(self.page, "app_name"),
            size=34,
            weight=ft.FontWeight.W_700,
            color=T.PRIMARY,
        )

        body = []
        if logo:
            body.append(logo)
        body += [
            heading,
            self.subtitle,
            self.name_field,
            self.email_field,
            self.password_field,
            self.action_button,
            self.msg_bar,
        ]

        w = viewport_width(self.page)
        col_width = min(380, max(280, int(w * 0.92))) if w else 360
        return ft.Column(
            controls=body,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
            width=col_width,
        )

    def _handle_action(self, e):
        name = (self.name_field.value or "").strip() if self.is_register else ""
        email = (self.email_field.value or "").strip().lower()
        password = self.password_field.value or ""

        if self.is_register:
            if not name:
                self.msg_bar.show_error(t(self.page, "invalid_name"))
                return
            if not EMAIL_RE.match(email):
                self.msg_bar.show_error(t(self.page, "invalid_email"))
                return
            if len(password) < 4:
                self.msg_bar.show_error(t(self.page, "invalid_password"))
                return
            user_id = create_user(name, email, password)
            if user_id is None:
                self.msg_bar.show_error(t(self.page, "email_exists"))
                return
            self.page.session.store.set("user_id", user_id)
            self.page.session.store.set("user_name", name)
            log_action(user_id, "register", f"email={email}")
            self.msg_bar.show_success(t(self.page, "register_success"))
        else:
            if not EMAIL_RE.match(email):
                self.msg_bar.show_error(t(self.page, "invalid_email"))
                return
            user = authenticate_user(email, password)
            if user is None:
                log_action(None, "login_failed", f"email={email}")
                self.msg_bar.show_error(t(self.page, "wrong_credentials"))
                return
            self.page.session.store.set("user_id", user["id"])
            self.page.session.store.set("user_name", user["name"])
            log_action(user["id"], "login", f"email={email}")
            self.msg_bar.show_success(t(self.page, "login_success"))

        self.on_login_success()