import logging
import os
import sqlite3

import bcrypt

logger = logging.getLogger("app.database")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    quantity REAL DEFAULT 0,
    price REAL DEFAULT 0,
    buying_price REAL DEFAULT 0,
    category TEXT DEFAULT '',
    packaging TEXT DEFAULT '',
    description TEXT DEFAULT '',
    low_stock_qty REAL DEFAULT 5,
    supplier_name TEXT DEFAULT '',
    supplier_whatsapp TEXT DEFAULT '',
    supplier_email TEXT DEFAULT '',
    barcode TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('in', 'out')),
    quantity REAL NOT NULL,
    date TEXT DEFAULT (datetime('now')),
    note TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    amount REAL NOT NULL,
    category TEXT DEFAULT '',
    date TEXT DEFAULT (datetime('now')),
    description TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS credit_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    total_amount REAL NOT NULL,
    paid_amount REAL DEFAULT 0,
    status TEXT CHECK (status IN ('open', 'closed')) DEFAULT 'open',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS credit_note_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    credit_note_id INTEGER NOT NULL REFERENCES credit_notes(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_price REAL NOT NULL,
    total_price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS credit_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    credit_note_id INTEGER NOT NULL REFERENCES credit_notes(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    date TEXT DEFAULT (datetime('now')),
    note TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_products_user ON products(user_id);
CREATE INDEX IF NOT EXISTS idx_movements_user ON stock_movements(user_id);
CREATE INDEX IF NOT EXISTS idx_movements_product ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_user ON credit_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_customer ON credit_notes(customer_id);
"""


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = _connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def user_count():
    conn = _connect()
    try:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()


def create_user(name, email, password):
    conn = _connect()
    try:
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            return None
        cur = conn.execute(
            "INSERT INTO users(name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hash_password(password)),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def authenticate_user(email, password):
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not row:
            return None
        if not check_password(password, row["password_hash"]):
            return None
        return dict(row)
    finally:
        conn.close()


def get_user(user_id):
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def add_product(user_id, name, quantity=0, price=0, buying_price=0, category="",
                packaging="", description="", low_stock_qty=5, supplier_name="",
                supplier_whatsapp="", supplier_email="", barcode=""):
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO products(user_id, name, quantity, price, buying_price, category, "
            "packaging, description, low_stock_qty, supplier_name, supplier_whatsapp, "
            "supplier_email, barcode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, name, quantity, price, buying_price, category, packaging, description,
             low_stock_qty, supplier_name, supplier_whatsapp, supplier_email, barcode),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_product(product_id, name, quantity=0, price=0, buying_price=0, category="",
                   packaging="", description="", low_stock_qty=5, supplier_name="",
                   supplier_whatsapp="", supplier_email="", barcode="", user_id=None):
    conn = _connect()
    try:
        if user_id is None:
            conn.execute(
                "UPDATE products SET name = ?, quantity = ?, price = ?, buying_price = ?, "
                "category = ?, packaging = ?, description = ?, low_stock_qty = ?, "
                "supplier_name = ?, supplier_whatsapp = ?, supplier_email = ?, barcode = ?, "
                "updated_at = datetime('now') WHERE id = ?",
                (name, quantity, price, buying_price, category, packaging, description,
                 low_stock_qty, supplier_name, supplier_whatsapp, supplier_email, barcode,
                 product_id),
            )
        else:
            conn.execute(
                "UPDATE products SET name = ?, quantity = ?, price = ?, buying_price = ?, "
                "category = ?, packaging = ?, description = ?, low_stock_qty = ?, "
                "supplier_name = ?, supplier_whatsapp = ?, supplier_email = ?, barcode = ?, "
                "updated_at = datetime('now') WHERE id = ? AND user_id = ?",
                (name, quantity, price, buying_price, category, packaging, description,
                 low_stock_qty, supplier_name, supplier_whatsapp, supplier_email, barcode,
                 product_id, user_id),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def delete_product(product_id, user_id=None):
    conn = _connect()
    try:
        if user_id is None:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        else:
            conn.execute("DELETE FROM products WHERE id = ? AND user_id = ?",
                         (product_id, user_id))
        conn.commit()
        return True
    finally:
        conn.close()


def get_products(user_id):
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM products WHERE user_id = ? ORDER BY name COLLATE NOCASE",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_product(product_id, user_id=None):
    conn = _connect()
    try:
        if user_id is None:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM products WHERE id = ? AND user_id = ?",
                (product_id, user_id),
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_product_by_barcode(barcode, user_id):
    if not barcode:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM products WHERE user_id = ? AND barcode = ?",
            (user_id, barcode),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Stock Movements
# ---------------------------------------------------------------------------

def add_stock_movement(product_id, user_id, mtype, quantity, note=""):
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        return False
    if mtype not in ("in", "out") or quantity <= 0:
        return False
    success = False
    conn = _connect()
    try:
        conn.execute("BEGIN")
        product = conn.execute(
            "SELECT * FROM products WHERE id = ? AND user_id = ?",
            (product_id, user_id),
        ).fetchone()
        if not product:
            conn.rollback()
            return False
        if mtype == "out":
            current = product["quantity"]
            if quantity > current:
                conn.rollback()
                return False
            new_qty = current - quantity
        else:
            new_qty = product["quantity"] + quantity
        conn.execute(
            "INSERT INTO stock_movements(product_id, user_id, type, quantity, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (product_id, user_id, mtype, quantity, note),
        )
        conn.execute(
            "UPDATE products SET quantity = ?, updated_at = datetime('now') WHERE id = ?",
            (new_qty, product_id),
        )
        conn.execute("COMMIT")
        success = True
    except Exception:
        logger.exception("add_stock_movement failed")
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()
    return success


def get_stock_movements(user_id, limit=50):
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT sm.*, p.name AS product_name FROM stock_movements sm "
            "JOIN products p ON p.id = sm.product_id "
            "WHERE sm.user_id = ? ORDER BY sm.date DESC, sm.id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stock_movements_by_product(user_id, product_id, limit=50):
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT sm.*, p.name AS product_name FROM stock_movements sm "
            "JOIN products p ON p.id = sm.product_id "
            "WHERE sm.user_id = ? AND sm.product_id = ? "
            "ORDER BY sm.date DESC, sm.id DESC LIMIT ?",
            (user_id, product_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def record_sale(user_id, product_id, quantity, note="sale"):
    """Sell stock: deduct quantity, log a stock_out movement and create an
    income transaction in one atomic transaction. Uses selling price."""
    done = False
    conn = _connect()
    try:
        conn.execute("BEGIN")
        product = conn.execute(
            "SELECT * FROM products WHERE id = ? AND user_id = ?",
            (product_id, user_id),
        ).fetchone()
        if not product:
            conn.rollback()
            return False
        if quantity > product["quantity"] or quantity <= 0:
            conn.rollback()
            return False
        new_qty = product["quantity"] - quantity
        conn.execute(
            "UPDATE products SET quantity = ?, updated_at = datetime('now') WHERE id = ?",
            (new_qty, product_id),
        )
        conn.execute(
            "INSERT INTO stock_movements(product_id, user_id, type, quantity, note) "
            "VALUES (?, ?, 'out', ?, ?)",
            (product_id, user_id, quantity, note),
        )
        amount = quantity * product["price"]
        conn.execute(
            "INSERT INTO transactions(user_id, type, amount, category, description) "
            "VALUES (?, 'income', ?, 'Sale', ?)",
            (user_id, amount, product["name"]),
        )
        conn.execute("COMMIT")
        done = True
    except Exception:
        logger.exception("record_sale failed")
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()
    return done


def add_transaction(user_id, ttype, amount, category="", description=""):
    if ttype not in ("income", "expense"):
        return None
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return None
    if amount <= 0:
        return None
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO transactions(user_id, type, amount, category, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, ttype, amount, category, description),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_transactions(user_id, limit=50):
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM transactions WHERE user_id = ? "
            "ORDER BY date DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

def add_customer(user_id, name, phone=""):
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO customers(user_id, name, phone) VALUES (?, ?, ?)",
            (user_id, name, phone),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_customers(user_id):
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM customers WHERE user_id = ? ORDER BY name COLLATE NOCASE",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_customer(customer_id, user_id=None):
    conn = _connect()
    try:
        if user_id is None:
            row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM customers WHERE id = ? AND user_id = ?",
                (customer_id, user_id),
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Credit Notes
# ---------------------------------------------------------------------------

def add_credit_note(user_id, customer_id, items, initial_paid=0.0):
    """Create a credit note, deducting stock and logging stock_out movements.
    items: list of (product_id, name, qty, unit_price, total_price).
    Returns (credit_note_id, ok, message)."""
    if not items:
        return None, False, "items"
    try:
        initial_paid = float(initial_paid or 0)
    except (TypeError, ValueError):
        return None, False, "error"
    if initial_paid < 0:
        return None, False, "error"
    conn = _connect()
    try:
        conn.execute("BEGIN")
        # Customer must belong to this user.
        owner = conn.execute(
            "SELECT id FROM customers WHERE id = ? AND user_id = ?",
            (customer_id, user_id),
        ).fetchone()
        if not owner:
            conn.rollback()
            return None, False, "customer"
        # Validate items before writing anything.
        for product_id, name, qty, unit_price, total_price in items:
            try:
                qty = float(qty)
                unit_price = float(unit_price)
            except (TypeError, ValueError):
                conn.rollback()
                return None, False, "error"
            if qty <= 0 or unit_price < 0:
                conn.rollback()
                return None, False, "error"
        total = sum(float(item[4]) for item in items)
        if total <= 0:
            conn.rollback()
            return None, False, "error"
        if initial_paid - total > 0.001:
            conn.rollback()
            return None, False, "exceeds"
        cur = conn.execute(
            "INSERT INTO credit_notes(user_id, customer_id, total_amount, paid_amount, "
            "status) VALUES (?, ?, ?, ?, ?)",
            (user_id, customer_id, total, initial_paid,
             "closed" if (total - initial_paid) < 0.001 else "open"),
        )
        cn_id = cur.lastrowid
        for product_id, name, qty, unit_price, total_price in items:
            conn.execute(
                "INSERT INTO credit_note_items(credit_note_id, product_id, product_name, "
                "quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?, ?)",
                (cn_id, product_id, name, qty, unit_price, total_price),
            )
            if product_id is not None:
                product = conn.execute(
                    "SELECT * FROM products WHERE id = ? AND user_id = ?",
                    (product_id, user_id),
                ).fetchone()
                if not product or qty > product["quantity"]:
                    conn.rollback()
                    return None, False, "stock"
                new_qty = product["quantity"] - qty
                conn.execute(
                    "UPDATE products SET quantity = ?, updated_at = datetime('now') "
                    "WHERE id = ?",
                    (new_qty, product_id),
                )
                conn.execute(
                    "INSERT INTO stock_movements(product_id, user_id, type, quantity, note) "
                    "VALUES (?, ?, 'out', ?, ?)",
                    (product_id, user_id, qty, "credit"),
                )
        conn.execute("COMMIT")
        return cn_id, True, ""
    except Exception:
        logger.exception("add_credit_note failed (user_id=%s)", user_id)
        try:
            conn.rollback()
        except Exception:
            pass
        return None, False, "error"
    finally:
        conn.close()


def get_credit_notes(user_id, status=None):
    conn = _connect()
    try:
        if status:
            rows = conn.execute(
                "SELECT cn.*, c.name AS customer_name FROM credit_notes cn "
                "JOIN customers c ON c.id = cn.customer_id "
                "WHERE cn.user_id = ? AND cn.status = ? "
                "ORDER BY cn.created_at DESC, cn.id DESC",
                (user_id, status),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT cn.*, c.name AS customer_name FROM credit_notes cn "
                "JOIN customers c ON c.id = cn.customer_id "
                "WHERE cn.user_id = ? ORDER BY cn.created_at DESC, cn.id DESC",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_credit_note(cn_id, user_id=None):
    conn = _connect()
    try:
        if user_id is None:
            row = conn.execute(
                "SELECT cn.*, c.name AS customer_name, c.phone AS customer_phone "
                "FROM credit_notes cn JOIN customers c ON c.id = cn.customer_id "
                "WHERE cn.id = ?",
                (cn_id,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT cn.*, c.name AS customer_name, c.phone AS customer_phone "
                "FROM credit_notes cn JOIN customers c ON c.id = cn.customer_id "
                "WHERE cn.id = ? AND cn.user_id = ?",
                (cn_id, user_id),
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_credit_note_items(cn_id, user_id=None):
    conn = _connect()
    try:
        if user_id is not None:
            owner = conn.execute(
                "SELECT id FROM credit_notes WHERE id = ? AND user_id = ?",
                (cn_id, user_id),
            ).fetchone()
            if not owner:
                return []
        rows = conn.execute(
            "SELECT * FROM credit_note_items WHERE credit_note_id = ?",
            (cn_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Credit Payments
# ---------------------------------------------------------------------------

def add_credit_payment(credit_note_id, amount, note="", user_id=None):
    """Record a payment; auto-close the note when fully paid; create income tx."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return None, False, "error"
    if amount <= 0:
        return None, False, "error"
    done = False
    conn = _connect()
    try:
        conn.execute("BEGIN")
        note_row = conn.execute(
            "SELECT * FROM credit_notes WHERE id = ?", (credit_note_id,)
        ).fetchone()
        if not note_row:
            conn.rollback()
            return None, False, "notfound"
        if user_id is not None and note_row["user_id"] != user_id:
            conn.rollback()
            return None, False, "notfound"
        remaining = note_row["total_amount"] - note_row["paid_amount"]
        if amount > remaining + 0.001:
            conn.rollback()
            return None, False, "exceeds"
        new_paid = note_row["paid_amount"] + amount
        new_status = "closed" if (note_row["total_amount"] - new_paid) < 0.001 else "open"
        cur = conn.execute(
            "INSERT INTO credit_payments(credit_note_id, amount, note) VALUES (?, ?, ?)",
            (credit_note_id, amount, note),
        )
        conn.execute(
            "UPDATE credit_notes SET paid_amount = ?, status = ?, "
            "updated_at = datetime('now') WHERE id = ?",
            (new_paid, new_status, credit_note_id),
        )
        conn.execute(
            "INSERT INTO transactions(user_id, type, amount, category, description) "
            "VALUES (?, 'income', ?, ?, ?)",
            (note_row["user_id"], amount, "Credit",
             f"CN #{credit_note_id} " + (note or "")),
        )
        conn.execute("COMMIT")
        done = True
    except Exception:
        logger.exception(
            "add_credit_payment failed (credit_note_id=%s)", credit_note_id
        )
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()
    return (cur.lastrowid if done else None), done, ("" if done else "error")


def get_credit_payments(credit_note_id, user_id=None):
    conn = _connect()
    try:
        if user_id is not None:
            owner = conn.execute(
                "SELECT id FROM credit_notes WHERE id = ? AND user_id = ?",
                (credit_note_id, user_id),
            ).fetchone()
            if not owner:
                return []
        rows = conn.execute(
            "SELECT * FROM credit_payments WHERE credit_note_id = ? "
            "ORDER BY date DESC, id DESC",
            (credit_note_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Aggregations
# ---------------------------------------------------------------------------

def get_credit_summary(user_id):
    conn = _connect()
    try:
        open_row = conn.execute(
            "SELECT COUNT(*) AS cnt, COALESCE(SUM(total_amount - paid_amount), 0) AS due "
            "FROM credit_notes WHERE user_id = ? AND status = 'open'",
            (user_id,),
        ).fetchone()
        return {"total_outstanding": float(open_row["due"] or 0),
                "open_count": int(open_row["cnt"] or 0)}
    finally:
        conn.close()


def get_dashboard_data(user_id):
    conn = _connect()
    try:
        stock = conn.execute(
            "SELECT COALESCE(SUM(quantity * price), 0) AS value, "
            "COALESCE(SUM(quantity * buying_price), 0) AS cost, "
            "COUNT(*) AS count, "
            "COALESCE(SUM(CASE WHEN quantity <= low_stock_qty THEN 1 ELSE 0 END), 0) "
            "AS low_stock "
            "FROM products WHERE user_id = ?", (user_id,),
        ).fetchone()
        cash = conn.execute(
            "SELECT COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) "
            "AS income, "
            "COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) "
            "AS expense FROM transactions WHERE user_id = ?", (user_id,),
        ).fetchone()
        credit = conn.execute(
            "SELECT COALESCE(SUM(total_amount - paid_amount), 0) AS due "
            "FROM credit_notes WHERE user_id = ? AND status = 'open'", (user_id,),
        ).fetchone()
        stock_value = float(stock["value"] or 0)
        buying_cost = float(stock["cost"] or 0)
        cash_income = float(cash["income"] or 0)
        cash_expense = float(cash["expense"] or 0)
        return {
            "stock_value": stock_value,
            "buying_cost": buying_cost,
            "potential_profit": stock_value - buying_cost,
            "cash_balance": cash_income - cash_expense,
            "low_stock_count": int(stock["low_stock"] or 0),
            "product_count": int(stock["count"] or 0),
            "cash_income": cash_income,
            "cash_expense": cash_expense,
            "credit_outstanding": float(credit["due"] or 0),
        }
    finally:
        conn.close()