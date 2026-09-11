import flet as ft

PRIMARY = "#00897B"
ACCENT = "#FF5722"
ERROR = "#D32F2F"
SUCCESS = "#388E3C"
WARNING = "#F57C00"
LOW_STOCK = "#FF6F00"
BG_DARK = "#121212"
BG_LIGHT = "#F5F5F5"
SURFACE_DARK = "#1E1E1E"
SURFACE_LIGHT = "#FFFFFF"
TEXT_DARK = "#E0E0E0"
TEXT_LIGHT = "#212121"

ARABIC_FONT = "VIP Rawy Thin"
LATIN_FONT = "Comfortaa"
NUMBER_FONT = LATIN_FONT

STATUS_COLORS = {
    "income": SUCCESS,
    "expense": ERROR,
    "in": SUCCESS,
    "out": ERROR,
    "open": WARNING,
    "closed": SUCCESS,
    "low": LOW_STOCK,
}


class AppTheme:
    @staticmethod
    def get_theme(theme_mode, lang):
        dark = theme_mode == "dark"
        bg = BG_DARK if dark else BG_LIGHT
        surface = SURFACE_DARK if dark else SURFACE_LIGHT
        text_color = TEXT_DARK if dark else TEXT_LIGHT

        def _style(fs, w=ft.FontWeight.W_400):
            return ft.TextStyle(size=fs, weight=w, color=text_color)

        colors = ft.ColorScheme(
            primary=PRIMARY,
            on_primary="#FFFFFF",
            secondary=ACCENT,
            on_secondary="#FFFFFF",
            error=ERROR,
            on_error="#FFFFFF",
            surface=surface,
            on_surface=text_color,
            on_surface_variant=text_color,
            outline="#888888",
            surface_container=surface,
            surface_container_high=surface,
            surface_container_highest=surface,
            surface_container_low=surface,
            surface_container_lowest=bg,
            surface_dim=bg,
        )

        return ft.Theme(
            color_scheme_seed=PRIMARY,
            font_family=ARABIC_FONT if lang == "ar" else LATIN_FONT,
            color_scheme=colors,
            text_theme=ft.TextTheme(
                display_large=_style(57, ft.FontWeight.W_700),
                display_medium=_style(45, ft.FontWeight.W_700),
                display_small=_style(36, ft.FontWeight.W_700),
                headline_large=_style(32, ft.FontWeight.W_600),
                headline_medium=_style(28, ft.FontWeight.W_600),
                headline_small=_style(24, ft.FontWeight.W_600),
                title_large=_style(22, ft.FontWeight.W_500),
                title_medium=_style(16, ft.FontWeight.W_500),
                title_small=_style(14, ft.FontWeight.W_500),
                body_large=_style(16),
                body_medium=_style(14),
                body_small=_style(12),
                label_large=_style(14, ft.FontWeight.W_500),
                label_medium=_style(12, ft.FontWeight.W_500),
                label_small=_style(11, ft.FontWeight.W_400),
            ),
        )