import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import app.database as db
from app import barcode as bc
import app.printing as printing

db.DB_PATH = os.path.join(tempfile.gettempdir(), "eshop_smoke_test.db")
if os.path.exists(db.DB_PATH):
    os.remove(db.DB_PATH)

db.init_db()
assert db.DB_PATH and os.path.exists(db.DB_PATH), "db file missing"

# first-run auth
assert db.user_count() == 0
uid = db.create_user("Admin", "admin@eshop.ma", "secret1")
assert uid, "create_user failed"
assert db.user_count() == 1
assert db.create_user("Dup", "admin@eshop.ma", "x") is None, "dup email allowed"
u = db.authenticate_user("admin@eshop.ma", "secret1")
assert u and u["id"] == uid, "auth failed"
assert db.authenticate_user("admin@eshop.ma", "bad") is None
assert db.check_password("secret1", db.hash_password("secret1"))

# products
pid1 = db.add_product(uid, "Lait 1L", quantity=20, price=9.5, buying_price=7.0,
                      category="laiticult", low_stock_qty=5)
pid2 = db.add_product(uid, "Pain", quantity=3, price=1.5, buying_price=1.0,
                      category="boulangerie")
assert len(db.get_products(uid)) == 2
p = db.get_product(pid1)
assert p["quantity"] == 20 and p["price"] == 9.5

# barcode
code = db.get_product_by_barcode("ED40404040", uid)
assert code is None
code = bc.generate_unique_code()
assert code.startswith("ED") and len(code) == 10

# stock movement in
assert db.add_stock_movement(pid2, uid, "in", 7, "livraison")
assert db.get_product(pid2)["quantity"] == 10
# stock movement out with validation
assert not db.add_stock_movement(pid2, uid, "out", 99, "impossible")
assert db.add_stock_movement(pid2, uid, "out", 2, "casse")
assert db.get_product(pid2)["quantity"] == 8
moves = db.get_stock_movements(uid, limit=50)
assert len(moves) == 2 and moves[0]["product_name"] == "Pain"

# sale (atomic: stock out + income)
assert db.record_sale(uid, pid1, 4)
assert db.get_product(pid1)["quantity"] == 16
assert not db.record_sale(uid, pid1, 999)
txs = db.get_transactions(uid)
assert len(txs) == 1 and txs[0]["type"] == "income" and txs[0]["amount"] == 38.0

# cash transactions
db.add_transaction(uid, "expense", 5.5, "Transport", "taxi")
db.add_transaction(uid, "income", 100, "Vente", "cash sale")

# customers + credit note
cid = db.add_customer(uid, "Ahmed", "0600000000")
assert cid
items = [(pid1, "Lait 1L", 2, 9.5, 19.0), (pid2, "Pain", 3, 1.5, 4.5)]
cn_id, ok, err = db.add_credit_note(uid, cid, items, initial_paid=0)
assert ok and cn_id, f"credit note failed: {err}"
assert db.get_product(pid1)["quantity"] == 14
assert db.get_product(pid2)["quantity"] == 5
assert not db.add_credit_note(uid, cid, [(pid1, "Lait", 999, 1, 999)])[1], "overstock"

note = db.get_credit_note(cn_id)
assert note["status"] == "open" and note["total_amount"] == 23.5
assert len(db.get_credit_note_items(cn_id)) == 2

# payments + auto income + auto close
assert not db.add_credit_payment(cn_id, 99, "too much")[1]
pay_id, ok2, _ = db.add_credit_payment(cn_id, 10, "avance")
assert ok2
note = db.get_credit_note(cn_id)
assert note["paid_amount"] == 10 and note["status"] == "open"
db.add_credit_payment(cn_id, 13.5, "solde")
note = db.get_credit_note(cn_id)
assert note["status"] == "closed", "note did not auto-close"
payments = db.get_credit_payments(cn_id)
assert len(payments) == 2

# income transaction auto-created for payments (category Credit)
credit_txs = [tx for tx in db.get_transactions(uid) if tx["category"] == "Credit"]
assert len(credit_txs) == 2, "missing auto income tx for payments"

# credit summary
sm = db.get_credit_summary(uid)
assert sm["open_count"] == 0 and sm["total_outstanding"] == 0

# second open note for summary test
cn2, ok3, _ = db.add_credit_note(uid, cid, [(pid2, "Pain", 2, 1.5, 3.0)])
assert ok3
sm = db.get_credit_summary(uid)
assert sm["open_count"] == 1 and abs(sm["total_outstanding"] - 3.0) < 0.001

# dashboard data
d = db.get_dashboard_data(uid)
assert d["cash_balance"] == 100 + 38 - 5.5 + 23.5  # income - expense
assert d["product_count"] == 2
assert d["low_stock_count"] == 1  # Pain 3 <= 5
assert abs(d["potential_profit"] - d["stock_value"] + d["buying_cost"]) < 0.001

# update / delete
db.update_product(pid2, "Pain complet", quantity=5, price=2.0, buying_price=1.2,
                  low_stock_qty=3)
p = db.get_product(pid2)
assert p["name"] == "Pain complet" and abs(p["price"] - 2.0) < 0.001
db.delete_product(pid1)
assert len(db.get_products(uid)) == 1
assert db.get_product(pid1) is None
assert not db.get_stock_movements_by_product(uid, pid1)  # cascaded

# barcode + PDF (patch opener so no viewer pops up)
b1, w1, h1 = bc.barcode_rgb_bytes("ED12345678", width=300, max_height=90)
assert len(b1) > 500 and w1 > 0 and h1 > 0
printed = []
orig_open = printing.open_with_default_viewer
printing.open_with_default_viewer = lambda path: printed.append(path)
try:
    out = printing.print_stickers([
        {"name": "Lait pasteurise 1L demi-ecreme", "price": 9.5, "barcode": "ED12345678"},
        {"name": "Pain complet long nom tres tres long", "price": 2.0, "barcode": "ED87654321"},
    ], currency_symbol="MAD")
    assert out and os.path.exists(out), "PDF not created"
    assert out in printed
    assert os.path.getsize(out) > 1000, "PDF suspiciously small"
finally:
    printing.open_with_default_viewer = orig_open

print("SMOKE TEST ALL PASS")
os.remove(db.DB_PATH)