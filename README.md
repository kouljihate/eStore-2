# eShop — POS / Inventory Management

A desktop POS & inventory app built with [Flet](https://flet.dev/) and SQLite.
Supports stock management, sales, credit sales (deferred payments), cash
register tracking (seed/movements/daily totals), and barcode sticker printing.

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

- Login / registration / user management (bcrypt-hashed passwords, session lock)
- Responsive layout: mobile default (390×844), side navigation rail on
  tablet/desktop, bottom navigation on phone, horizontally-scrollable tables
- Arabic / French / English UI (RTL support) with session-wide language switch
- Stock: products (barcode, quantity, cost/price, stock alerts), buy/sell,
  credit sales, stock movements & price history
- Credit: multi-item credit notes, per-customer balance, payments, auto-close on settlement
- Cash: daily categorization, seed money, running balance, monthly close
- Settings: theme, language, currency, daily numbers format ("ث-م"/"M-AM")
- Barcode: product labels encoded as `ED` + 8-digit Code128
- Printing: A5/A4 sticker-sheet PDF via fpdf2 (opens in the default viewer)

## Font note

The app registers custom fonts from `assets/fonts/` (value paths are relative
to the assets dir, per Flet's font loading):

- **Arabic UI**: `VIP RAWY THIN THIN` — `assets/fonts/VIPRawyThinThin.ttf`.
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
  logging_config.py      logging setup (rotating file + console, excepthook)
  responsive.py          viewport helpers: breakpoints, padding, hscroll
  database.py            SQLite schema + CRUD + atomic sale recording
  translations.py        UI strings (ar/fr/en) + format helpers
  theme.py               ColorScheme + component styling per language/theme
  currency.py            currency codes & formatting
  barcode.py             Code128 PNG generation
  printing.py            sticker-sheet PDF generation
  message_bar.py         toast/inline message widget
  screens/               login, dashboard, stock, cash, credit, settings
scripts/
  smoke_test.py          CLI checks: DB ops, barcode, PDF, translations
  ui_build_test.py       in-memory UI build test (no display needed)
```

## Logs

The app logs to `logs/app.log` (rotating, 5 × 5 MB) and the console.
Uncaught exceptions are captured with full tracebacks. On startup it logs the
app version and build date; database transaction failures are logged with
their error context.

## Tests

```bash
python scripts\smoke_test.py
python scripts\ui_build_test.py
```