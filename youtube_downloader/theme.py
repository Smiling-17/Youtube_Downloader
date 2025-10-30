"""Tkinter theming helpers."""

from __future__ import annotations

try:
    from tkinter import ttk
except ImportError:  # pragma: no cover - platform without tkinter
    ttk = None  # type: ignore[assignment]


class ColorTheme:
    """Centralised color palette for the GUI."""

    PRIMARY_BLUE = "#87CEEB"
    PRIMARY_PINK = "#FFB6C1"
    SECONDARY_BLUE = "#B0E0E6"
    SECONDARY_PINK = "#FFCCCB"

    BACKGROUND = "#F8F9FA"
    CARD_BACKGROUND = "#FFFFFF"
    FRAME_BACKGROUND = "#F0F8FF"

    TEXT_PRIMARY = "#2C3E50"
    TEXT_SECONDARY = "#5D6D7E"
    TEXT_SUCCESS = "#27AE60"
    TEXT_ERROR = "#E74C3C"
    TEXT_WARNING = "#F39C12"

    BUTTON_PRIMARY = "#4A90E2"
    BUTTON_SUCCESS = "#5CB85C"
    BUTTON_WARNING = "#F0AD4E"
    BUTTON_DANGER = "#D9534F"
    BUTTON_HOVER = "#357ABD"

    BORDER_LIGHT = "#E1E8ED"
    BORDER_MEDIUM = "#AAB8C2"
    BORDER_FOCUS = "#4A90E2"


class ModernStyle:
    """Provide modern styles for ttk widgets."""

    @staticmethod
    def configure_ttk_style() -> "ttk.Style":
        if ttk is None:
            raise RuntimeError("tkinter is not available on this system.")

        style = ttk.Style()

        style.configure(
            "Modern.TFrame",
            background=ColorTheme.FRAME_BACKGROUND,
            relief="flat",
            borderwidth=1,
        )

        style.configure(
            "Card.TFrame",
            background=ColorTheme.CARD_BACKGROUND,
            relief="solid",
            borderwidth=1,
        )

        style.configure(
            "Modern.TLabelframe",
            background=ColorTheme.FRAME_BACKGROUND,
            relief="flat",
            borderwidth=1,
            labeloutside=False,
            padding=10,
        )

        style.configure(
            "Modern.TLabelframe.Label",
            background=ColorTheme.FRAME_BACKGROUND,
            foreground=ColorTheme.TEXT_PRIMARY,
            font=("Segoe UI", 9),
            padding=[20, 10],
        )

        style.map(
            "Modern.TNotebook.Tab",
            background=[
                ("selected", ColorTheme.PRIMARY_BLUE),
                ("active", ColorTheme.PRIMARY_PINK),
            ],
        )

        return style
