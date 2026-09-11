import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft

import main as app_main

if __name__ == "__main__":
    ft.run(
        main=app_main.main,
        name="eShop",
        assets_dir="assets",
        view=ft.AppView.WEB_BROWSER,
        port=4050,
    )