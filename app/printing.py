import io
import os
import subprocess
import sys
import tempfile

from fpdf import FPDF

from app import barcode as bc

STICKER_W = 95
STICKER_H = 42
PAGE_W = 210
PAGE_H = 297
LEFT = 10
TOP = 12
COL_PITCH = 100
ROW_PITCH = 44
COLS = 2
ROWS_PER_PAGE = 5
PER_PAGE = COLS * ROWS_PER_PAGE
MAX_NAME_CHARS = 28


def _truncate(name):
    name = str(name).strip()
    return name[:MAX_NAME_CHARS]


def open_with_default_viewer(path):
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.call(["open", path])
    else:
        subprocess.call(["xdg-open", path])


def print_stickers(products, currency_symbol="MAD"):
    """Generate an A4 sticker PDF from products and open it.
    products: list of dicts with keys name, price, barcode."""
    if not products:
        return None
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.set_margins(0, 0, 0)

    for idx, product in enumerate(products):
        if idx % PER_PAGE == 0:
            pdf.add_page()
        local = idx % PER_PAGE
        col = local % COLS
        row = local // COLS
        x = LEFT + col * COL_PITCH
        y = TOP + row * ROW_PITCH

        pdf.set_fill_color(250, 250, 250)
        pdf.rect(x, y, STICKER_W, STICKER_H, style="D")

        name = _truncate(product.get("name", ""))
        price = product.get("price", 0)
        code = product.get("barcode") or ""

        pdf.set_font("helvetica", "B", 13)
        pdf.set_text_color(30, 30, 30)
        pdf.set_xy(x + 4, y + 3)
        pdf.cell(STICKER_W - 8, 7, name)

        if price is not None:
            pdf.set_font("helvetica", "B", 15)
            pdf.set_text_color(0, 137, 123)
            price_text = f"{float(price):,.2f} {currency_symbol}"
            pdf.set_xy(x + 4, y + 11)
            pdf.cell(STICKER_W - 8, 7, price_text)

        if code:
            png_bytes, w, h = bc.barcode_rgb_bytes(code, width=700, max_height=130)
            img_w = STICKER_W - 12
            img_h = min(15.0, (img_w * h) / w)
            img_x = x + (STICKER_W - img_w) / 2
            pdf.image(io.BytesIO(png_bytes), x=img_x, y=y + 21, w=img_w, h=img_h)
            pdf.set_font("helvetica", "", 8)
            pdf.set_text_color(60, 60, 60)
            pdf.set_xy(x + 4, y + 37)
            pdf.cell(STICKER_W - 8, 4, code, align="C")

    output_dir = tempfile.gettempdir()
    output_path = os.path.join(output_dir, "eshop_stickers.pdf")
    pdf.output(output_path)
    open_with_default_viewer(output_path)
    return output_path