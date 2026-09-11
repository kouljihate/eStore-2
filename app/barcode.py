import base64
import io
import random

import barcode as barcode_lib
import flet as ft
from barcode.writer import ImageWriter
from PIL import Image

BARCODE_PREFIX = "ED"


def generate_unique_code():
    return f"{BARCODE_PREFIX}{random.randint(10000000, 99999999)}"


def generate_barcode_png(code):
    options = {
        "module_width": 0.24,
        "module_height": 11.0,
        "font_size": 11,
        "text_distance": 3.0,
        "quiet_zone": 3.0,
        "background": "white",
        "foreground": "black",
    }
    writer = ImageWriter()
    barcode_obj = barcode_lib.get("code128", code, writer=writer)
    buf = io.BytesIO()
    barcode_obj.write(buf, options=options)
    buf.seek(0)
    return buf.getvalue()


def _white_bg(png_bytes, target_width=512, max_height=220):
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.paste(img, (0, 0), img)
    if img.width > 0:
        ratio = target_width / img.width
        new_h = int(img.height * ratio)
        if new_h > max_height:
            ratio = max_height / img.height
            new_h = max_height
        new_w = max(1, int(img.width * ratio))
        bg = bg.convert("RGB").resize((new_w, new_h), Image.LANCZOS)
        return bg, new_w, new_h
    return bg.convert("RGB"), target_width, max_height


def barcode_rgb_bytes(code, width=512, max_height=220):
    """Return PNG bytes on a white background with the alpha channel flattened.
    Returns (png_bytes, width, height)."""
    raw = generate_barcode_png(code)
    png, w, h = _white_bg(raw, target_width=width, max_height=max_height)
    out = io.BytesIO()
    png.save(out, format="PNG")
    out.seek(0)
    return out.getvalue(), w, h


def barcode_base64(code, width=512, max_height=220):
    png, w, h = barcode_rgb_bytes(code, width=width, max_height=max_height)
    return base64.b64encode(png).decode("ascii"), w, h


def barcode_image(code, width=512, max_height=220):
    data, w, h = barcode_base64(code, width=width, max_height=max_height)
    return ft.Image(src_base64=data, width=w, height=h)