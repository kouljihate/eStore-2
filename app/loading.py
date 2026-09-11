import asyncio

import flet as ft

from app import theme as T


class LoadingDots:
    def __init__(self, page, color=None):
        self.page = page
        self._color = color or T.PRIMARY
        self._stop = False
        self._task = None
        self._dots = []
        self._build()

    def _build(self):
        self._dots = []
        for _ in range(3):
            self._dots.append(
                ft.Container(
                    width=12,
                    height=12,
                    bgcolor=self._dim(),
                    shape=ft.BoxShape.CIRCLE,
                )
            )

    def _dim(self):
        return f"{self._color}44"

    def _active(self, idx):
        for j, dot in enumerate(self._dots):
            if j == idx:
                dot.width = 16
                dot.height = 16
                dot.bgcolor = self._color
            else:
                dot.width = 12
                dot.height = 12
                dot.bgcolor = self._dim()

    def build(self):
        return ft.Row(
            controls=self._dots,
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def start(self):
        if self._task is not None:
            return
        self._stop = False
        self._task = self.page.run_task(self._loop)

    async def _loop(self):
        try:
            while not self._stop:
                for i in range(3):
                    if self._stop:
                        break
                    self._active(i)
                    try:
                        self.page.update()
                    except Exception:
                        return
                    await asyncio.sleep(0.22)
        finally:
            self._task = None

    def stop(self):
        self._stop = True
        self._task = None