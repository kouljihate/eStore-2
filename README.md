# eShop — POS / Inventory Management (v1.7.0)

A desktop POS & inventory app built with [Flet](https://flet.dev/) and SQLite.
Supports stock management, sales, credit sales (deferred payments), cash
tracking, and barcode sticker printing.

## Requirements

- Python 3.10+
- A display (Flet runs a desktop window)

## Install & Run

```bash
python -m pip install -r requirements.txt
python run.py          # or: python main.py
```

On first launch the database (`data/app.db`) is created automatically.
Since there are no users yet, the app opens on the **registration screen**
— create an admin account, then log in.

## Features

- Login / registration (bcrypt-hashed passwords)
- Responsive layout: bottom navigation on phone, side navigation rail on
  tablet/desktop, horizontally-scrollable tables
- Arabic / French / English UI (RTL support); language switch lives in the
  footer and retranslates everything (nav, screens, dialogs, footer, fonts)
- Footer: language selector + version badge, hideable via
  Settings → Display footer (yes/no)
- Dashboard: stock value, potential profit, cash balance, product/low-stock
  counts, credit outstanding, recent movements & transactions; friendly
  empty state for new accounts
- Stock: products (barcode, quantity, cost/price, stock alerts), sell,
  sell-on-credit, stock in/out movements & history; empty state with
  single + bulk product creation (5 rows per batch)
- Credit: multi-item credit notes, per-customer balance, payments,
  auto-close on settlement, overpay protection
- Cash: income/expense tracking with running balance
- Settings: theme (light/dark), footer visibility, currency
- Per-user data isolation (products, customers, notes scoped by owner)
- Barcode: product labels encoded as `ED` + 8-digit Code128
- Printing: A4 sticker-sheet PDF via fpdf2 (opens in the default viewer)

## Font note

The app registers custom fonts from `assets/fonts/` (value paths are relative
to the assets dir, per Flet's font loading):

- **Arabic UI**: `VIP Rawy Thin` — `assets/fonts/VIPRawyThinThin.ttf`.
  If the font is installed in the Windows fonts folder(s) instead, it is
  usable by family name without bundling.
- **English / French UI & all numbers (all languages)**: `Comfortaa` —
  static pair shipped at `assets/fonts/Comfortaa-Regular.ttf`.

When a file is missing, the app falls back to the system font.

## Project layout

```
main.py                  entry point (splash, auth gate, 5-tab navigation)
run.py                   launcher wrapper
app/
  version.py             app name, version, build date
  activity.py            user action/click logging helper
  logging_config.py      logging setup (rotating file + console, excepthook)
  responsive.py          viewport helpers: breakpoints, padding, hscroll
  database.py            SQLite schema + CRUD + atomic sale recording
  translations.py        UI strings (ar/fr/en) + format/category helpers
  theme.py               ColorScheme + component styling per language/theme
  currency.py            currency codes & formatting
  barcode.py             Code128 PNG generation
  printing.py            sticker-sheet PDF generation
  message_bar.py         toast/inline message widget
  loading.py             splash loading-dots animation
  screens/               login, dashboard, stock, cash, credit, settings
scripts/
  smoke_test.py          CLI checks: DB ops, barcode, PDF, translations
  ui_build_test.py       in-memory UI build test (no display needed)
```

## Logs

The app logs to `logs/app.log` (rotating, 5 × 5 MB) and the console.
Uncaught exceptions are captured with full tracebacks. On startup it logs the
app version and build date; database transaction failures are logged with
their error context. User actions (navigation, sales, payments, settings
changes…) are logged as `action=<name> user=<id> …` under `[app.actions]`.
Screen build failures are caught per-tab (red error card + traceback)
so one broken tab can never blank the app.

## Tests

```bash
python scripts\smoke_test.py
python scripts\ui_build_test.py
```