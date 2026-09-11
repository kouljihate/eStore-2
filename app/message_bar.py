import asyncio

import flet as ft

from app import theme as T


class MessageBar(ft.Row):
    def __init__(self, page):
        self._page = page
        self._label = ft.Text("", color=T.TEXT_DARK)
        self._container = ft.Container(
            content=self._label,
            bgcolor=T.SURFACE_DARK,
            border_radius=ft.BorderRadius.all(10),
            padding=ft.Padding.symmetric(horizontal=18, vertical=10),
            visible=False,
            shadow=ft.BoxShadow(blur_radius=8, color="#40000000", offset=ft.Offset(0, 2)),
        )
        super().__init__(
            controls=[self._container],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
        )
        self._run_id = 0

    def _show(self, message, color, icon=None):
        self._run_id += 1
        run_id = self._run_id
        if icon is not None:
            self._label.value = f"{icon}  {message}"
        else:
            self._label.value = message
        self._container.bgcolor = color
        self._container.visible = True
        self._page.update()
        self._page.run_task(self._hide_after, run_id)

    async def _hide_after(self, run_id):
        await asyncio.sleep(3)
        if run_id == self._run_id:
            self._container.visible = False
            self._page.update()

    def show_success(self, message):
        self._show(message, T.SUCCESS, "\u2714")

    def show_error(self, message):
        self._show(message, T.ERROR, "\u2716")

    def show_warning(self, message):
        self._show(message, T.WARNING, "\u26a0")

    def show_info(self, message):
        self._show(message, T.PRIMARY, "\u2139")