"""Headless web server entrypoint for hosting eShop on a Linux VM.

NOT a Flask/WSGI app (gunicorn cannot serve this project). Run with the
venv python; Flet serves the web UI on ESHOP_HOST:ESHOP_PORT:

    ESHOP_HOST=0.0.0.0 ESHOP_PORT=5003 venv/bin/python serve_web.py
"""

import os

import flet as ft

import main as app_main

HOST = os.environ.get("ESHOP_HOST", "0.0.0.0")
PORT = int(os.environ.get("ESHOP_PORT", "5003"))

if __name__ == "__main__":
    ft.run(
        main=app_main.main,
        name="eShop",
        assets_dir="assets",
        view=ft.AppView.WEB_BROWSER,
        host=HOST,
        port=PORT,
    )
