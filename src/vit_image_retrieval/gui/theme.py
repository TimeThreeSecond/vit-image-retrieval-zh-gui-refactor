"""Theme configuration for the ViT Image Retrieval GUI.

All visual styling lives here — change colors/fonts/spacing in one place.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Theme:
    """Centralized theme configuration."""

    # ── Colors ──
    bg_primary: str = "#ffffff"
    bg_secondary: str = "#f5f6f8"
    bg_tertiary: str = "#eef0f4"
    bg_hover: str = "#e8ecf4"
    text_primary: str = "#1a1d2e"
    text_secondary: str = "#555b6e"
    text_muted: str = "#8b92a8"
    border: str = "#d4d8e0"
    border_focus: str = "#3b6df0"

    # ── Accent ──
    accent: str = "#3b6df0"
    accent_hover: str = "#2b5cdb"
    accent_light: str = "rgba(59,109,240,0.10)"
    success: str = "#0d9488"
    success_light: str = "rgba(13,148,136,0.10)"
    warning: str = "#c2670a"
    warning_light: str = "rgba(194,103,10,0.10)"
    danger: str = "#d6336c"
    danger_light: str = "rgba(214,51,108,0.10)"

    # ── Font sizes (2× relative to original 11–18px) ──
    font_xs: str = "22px"
    font_sm: str = "24px"
    font_md: str = "26px"
    font_lg: str = "28px"
    font_xl: str = "32px"

    # ── Spacing ──
    padding_xs: str = "6px"
    padding_sm: str = "10px"
    padding_md: str = "16px"
    padding_lg: str = "24px"

    # ── Misc ──
    radius_sm: str = "6px"
    radius_md: str = "10px"
    radius_lg: str = "14px"

    # ── Scrollbar ──
    scrollbar_bg: str = "#f5f6f8"
    scrollbar_thumb: str = "#c0c5ce"
    scrollbar_thumb_hover: str = "#9ba0ab"

    # ── Style helpers ──

    @property
    def scrollbar_style(self) -> str:
        return f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                width: 8px; background: {self.scrollbar_bg}; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.scrollbar_thumb}; border-radius: 4px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {self.scrollbar_thumb_hover}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """

    def primary_btn(self, disabled: bool = False) -> str:
        if disabled:
            return f"""
                QPushButton {{
                    background: {self.bg_tertiary}; color: {self.text_muted};
                    border: 1px solid {self.border}; border-radius: {self.radius_md};
                    padding: {self.padding_sm} {self.padding_lg};
                    font-size: {self.font_md}; font-weight: 600;
                }}
            """
        return f"""
            QPushButton {{
                background: {self.accent}; color: white;
                border: none; border-radius: {self.radius_md};
                padding: {self.padding_sm} {self.padding_lg};
                font-size: {self.font_md}; font-weight: 600;
            }}
            QPushButton:hover {{ background: {self.accent_hover}; }}
            QPushButton:pressed {{ background: {self.accent}; }}
        """

    def secondary_btn(self) -> str:
        return f"""
            QPushButton {{
                background: {self.bg_primary}; color: {self.text_primary};
                border: 1px solid {self.border}; border-radius: {self.radius_md};
                padding: {self.padding_sm} {self.padding_lg};
                font-size: {self.font_md};
            }}
            QPushButton:hover {{ background: {self.bg_hover}; border-color: {self.accent}; }}
        """

    def success_btn(self) -> str:
        return f"""
            QPushButton {{
                background: {self.success}; color: white;
                border: none; border-radius: {self.radius_md};
                padding: {self.padding_sm} {self.padding_lg};
                font-size: {self.font_md}; font-weight: 600;
            }}
            QPushButton:hover {{ background: #0f766e; }}
        """

    def input_style(self) -> str:
        return f"""
            QLineEdit, QSpinBox {{
                padding: {self.padding_sm};
                border: 1px solid {self.border};
                border-radius: {self.radius_md};
                font-size: {self.font_md};
                background: {self.bg_primary};
                color: {self.text_primary};
            }}
            QLineEdit:focus, QSpinBox:focus {{
                border-color: {self.border_focus};
            }}
        """

    def label_style(self, bold: bool = False, size: Optional[str] = None) -> str:
        weight = "bold" if bold else "normal"
        sz = size or self.font_md
        return f"font-size: {sz}; font-weight: {weight}; color: {self.text_primary};"

    def info_panel_style(self) -> str:
        return f"""
            QLabel {{
                background: {self.bg_secondary};
                padding: {self.padding_sm};
                border-radius: {self.radius_md};
                font-size: {self.font_sm};
                color: {self.text_secondary};
            }}
        """

    def badge_style(self, bg: str, fg: str) -> str:
        return f"""
            QLabel {{
                background: {bg}; color: {fg};
                padding: 3px 10px;
                border-radius: {self.radius_sm};
                font-size: {self.font_sm};
                font-weight: 600;
            }}
        """


# ── Built-in themes ──
LIGHT = Theme()
