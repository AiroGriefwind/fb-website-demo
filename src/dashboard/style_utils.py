from __future__ import annotations

from src.dashboard.config import CATEGORY_BASE_COLORS, CATEGORY_INTENSITY_OVERRIDES


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    clean = hex_color.strip().lstrip("#")
    if len(clean) != 6:
        return (128, 128, 128)
    return tuple(int(clean[i : i + 2], 16) for i in (0, 2, 4))


def mix_with_white(hex_color: str, color_ratio: float) -> str:
    r, g, b = hex_to_rgb(hex_color)
    ratio = max(0.0, min(1.0, color_ratio))
    wr = round(255 * (1 - ratio) + r * ratio)
    wg = round(255 * (1 - ratio) + g * ratio)
    wb = round(255 * (1 - ratio) + b * ratio)
    return f"#{wr:02X}{wg:02X}{wb:02X}"


def category_style_tokens(category: str) -> dict[str, str]:
    base = CATEGORY_BASE_COLORS.get(category, "#667085")
    intensity = CATEGORY_INTENSITY_OVERRIDES.get(category, {})
    header_ratio = float(intensity.get("header", 0.33))
    border_ratio = float(intensity.get("border", 0.52))
    card_ratio = float(intensity.get("card", 0.22))
    return {
        "base": base,
        "header_bg": mix_with_white(base, header_ratio),
        "header_border": mix_with_white(base, border_ratio),
        "card_bg": mix_with_white(base, card_ratio),
        "card_border": mix_with_white(base, max(card_ratio, 0.45)),
    }
