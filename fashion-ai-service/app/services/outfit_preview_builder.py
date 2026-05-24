"""
Outfit Preview Builder for Vouge.AI.
Programmatically composes a single vertically-aligned outfit preview image from
individual processed garment images (top, bottom, footwear, optional outerwear).

Design:
  - Canvas: 540 x 1440 pixels (portrait 1:2.67 ratio), deep charcoal background
  - Slot proportions:
      TOPS/OUTERWEAR:  460px wide, 480px tall  (top of frame)
      BOTTOMS:         440px wide, 500px tall  (middle)
      FOOTWEAR:        340px wide, 300px tall  (bottom)
  - Each garment is white-background-removed, composited with alpha masking
  - Premium footer bar with score badge and slot labels
"""
import io
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

logger = logging.getLogger("fashion-ai-service")

# ---------------------------------------------------------------------------
# Canvas & visual design constants
# ---------------------------------------------------------------------------
CANVAS_W = 540
CANVAS_H = 1440

# Slot definitions: (y_offset, max_w, max_h, label)
SLOT_CONFIGS: Dict[str, Tuple[int, int, int, str]] = {
    "TOPS":      (20,  460, 480, "TOP"),
    "OUTERWEAR": (20,  460, 480, "OUTERWEAR"),
    "BOTTOMS":   (530, 440, 500, "BOTTOM"),
    "FOOTWEAR":  (1060, 340, 300, "SHOES"),
}

# Premium dark-mode palette
BG_COLOR   = (13,  14,  18,  255)   # #0D0E12 near-black
CARD_COLOR = (22,  23,  30,  255)   # #16171E slate card
DIVIDER    = (40,  42,  54,  255)   # #282A36 subtle divider
ACCENT     = (168, 128, 255, 255)   # #A880FF violet accent
LABEL_FG   = (160, 163, 182, 255)   # muted grey text
WHITE      = (255, 255, 255, 255)

# Slot label strip
STRIP_H = 30
STRIP_COLORS = {
    "TOPS":      (60,  40,  100, 200),   # indigo-purple
    "OUTERWEAR": (40,  60,  100, 200),   # navy-purple
    "BOTTOMS":   (40,  80,  80,  200),   # teal-slate
    "FOOTWEAR":  (80,  60,  40,  200),   # warm amber-slate
}

# Score badge
BADGE_W, BADGE_H = 90, 90
BADGE_COLORS = {
    range(90, 101): (130, 215, 100),   # emerald-green  90-100
    range(75, 90):  (108, 180, 255),   # sky-blue       75-89
    range(60, 75):  (255, 200, 80),    # golden         60-74
    range(0,  60):  (200, 80,  80),    # soft-red       0-59
}


def _get_badge_color(score: int) -> Tuple[int, int, int]:
    for r, c in BADGE_COLORS.items():
        if score in r:
            return c
    return (200, 200, 200)


def _make_font(size: int) -> ImageFont.ImageFont:
    """
    Loads a system font at the given pixel size.
    Falls back gracefully to the Pillow default bitmap font if system fonts
    are unavailable.
    """
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/SF Pro.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _remove_white_background(img: Image.Image, tolerance: int = 240) -> Image.Image:
    """
    Converts a near-white background to fully transparent pixels.
    Works on RGB and RGBA source images.
    
    Args:
        img:       Source PIL Image
        tolerance: Pixel brightness threshold (0-255). Pixels with R, G, B all
                   above this value are considered background and turned transparent.
    Returns:
        RGBA image with white/near-white background eroded away.
    """
    rgba = img.convert("RGBA")
    data = rgba.load()
    w, h = rgba.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = data[x, y]
            # Classify as background if all channels are very bright
            if r >= tolerance and g >= tolerance and b >= tolerance:
                data[x, y] = (r, g, b, 0)   # fully transparent

    return rgba


def _paste_garment(
    canvas: Image.Image,
    garment_path: str,
    slot_key: str,
    center_x: int,
) -> None:
    """
    Loads, bg-strips, fits, and alpha-pastes a single garment onto the canvas.

    Args:
        canvas:       The composite RGBA canvas image to draw on.
        garment_path: Absolute path to the processed garment PNG on disk.
        slot_key:     One of TOPS, OUTERWEAR, BOTTOMS, FOOTWEAR.
        center_x:     Horizontal centre position on the canvas.
    """
    slot_cfg = SLOT_CONFIGS.get(slot_key)
    if slot_cfg is None:
        logger.warning(f"OutfitPreviewBuilder: unknown slot key '{slot_key}'. Skipping.")
        return

    y_offset, max_w, max_h, label = slot_cfg
    path = Path(garment_path)

    if not path.exists():
        logger.warning(f"OutfitPreviewBuilder: garment file missing at '{garment_path}'. Skipping slot {slot_key}.")
        return

    try:
        src = Image.open(path).convert("RGBA")

        # Erase white/near-white backgrounds (handles non-transparent PNGs)
        src_clean = _remove_white_background(src, tolerance=238)

        # Proportional resize to fit slot box
        src_clean.thumbnail((max_w, max_h), Image.LANCZOS)

        # Centre-align within slot
        paste_x = center_x - src_clean.width // 2
        paste_y = y_offset + (max_h - src_clean.height) // 2

        # Use the image's own alpha channel as mask
        canvas.paste(src_clean, (paste_x, paste_y), mask=src_clean)

    except Exception as err:
        logger.error(f"OutfitPreviewBuilder: failed to paste garment from '{garment_path}': {err}")


def _draw_slot_label_strip(
    draw: ImageDraw.ImageDraw,
    slot_key: str,
    canvas_w: int,
) -> None:
    """Draws a slim coloured label strip at the top of each garment slot zone."""
    cfg = SLOT_CONFIGS.get(slot_key)
    if not cfg:
        return
    y_offset, _, max_h, label = cfg
    color = STRIP_COLORS.get(slot_key, (60, 60, 80, 160))
    strip_y = y_offset
    draw.rectangle([(0, strip_y), (canvas_w, strip_y + STRIP_H)], fill=color)

    font = _make_font(13)
    draw.text((14, strip_y + 7), label.upper(), fill=(220, 220, 240, 255), font=font)


def _draw_score_badge(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    score: Optional[int],
) -> None:
    """Renders a circular score badge in the top-right corner."""
    if score is None:
        return

    badge_x = CANVAS_W - BADGE_W - 14
    badge_y = 14
    color = _get_badge_color(score)

    # Draw filled circle background
    draw.ellipse(
        [(badge_x, badge_y), (badge_x + BADGE_W, badge_y + BADGE_H)],
        fill=(*color, 200),
        outline=(*color, 255),
        width=3
    )

    # Draw score number
    score_str = str(score)
    font_big = _make_font(30)
    font_sm  = _make_font(11)

    # Rough centre calculation
    draw.text(
        (badge_x + BADGE_W // 2 - (len(score_str) * 9), badge_y + 18),
        score_str,
        fill=(255, 255, 255, 255),
        font=font_big
    )
    draw.text(
        (badge_x + BADGE_W // 2 - 12, badge_y + 58),
        "SCORE",
        fill=(220, 220, 240, 200),
        font=font_sm
    )


def _draw_footer(
    draw: ImageDraw.ImageDraw,
    occasion: Optional[str],
    season: Optional[str],
    reasoning_snippet: Optional[str],
) -> None:
    """Renders a subtle premium footer bar at the bottom of the canvas."""
    footer_y = CANVAS_H - 100
    draw.rectangle([(0, footer_y), (CANVAS_W, CANVAS_H)], fill=(18, 14, 28, 240))

    # Thin accent top-border line
    draw.rectangle([(0, footer_y), (CANVAS_W, footer_y + 2)], fill=ACCENT)

    font_brand  = _make_font(16)
    font_meta   = _make_font(12)
    font_reason = _make_font(11)

    # Brand label
    draw.text((16, footer_y + 10), "VOUGE.AI", fill=(168, 128, 255, 255), font=font_brand)

    # Meta tags (occasion / season)
    meta_parts = []
    if occasion:
        meta_parts.append(f"✦ {occasion.upper()}")
    if season:
        meta_parts.append(f"✦ {season.upper()}")
    if meta_parts:
        draw.text((16, footer_y + 33), "  ".join(meta_parts), fill=(160, 163, 182, 220), font=font_meta)

    # Reasoning snippet (first 80 chars)
    if reasoning_snippet:
        snippet = reasoning_snippet[:80].strip()
        if len(reasoning_snippet) > 80:
            snippet += "…"
        draw.text((16, footer_y + 55), snippet, fill=(120, 123, 145, 200), font=font_reason)


def _draw_vertical_separator(
    draw: ImageDraw.ImageDraw,
    y_pos: int,
    w: int,
) -> None:
    """Draws a subtle 1-pixel horizontal separator line between slots."""
    draw.line([(0, y_pos), (w, y_pos)], fill=DIVIDER, width=1)


class OutfitPreviewBuilder:
    """
    Composes a single vertically-aligned PNG outfit preview image from
    processed garment images.
    """

    @classmethod
    def build_preview(
        cls,
        outfit_items: List[Dict[str, Any]],
        score: Optional[int] = None,
        occasion: Optional[str] = None,
        season: Optional[str] = None,
        reasoning: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> bytes:
        """
        Builds and returns the composed outfit preview image as raw PNG bytes.
        Also optionally saves the file to `output_path` if provided.

        Args:
            outfit_items:  List of normalized item dicts containing 'category'
                           and 'processed_image_path' keys.
            score:         Outfit compatibility score (0-100) for badge display.
            occasion:      Occasion label for the footer bar.
            season:        Season label for the footer bar.
            reasoning:     Short stylist reasoning snippet for the footer.
            output_path:   If provided, the composed image is saved to this path.

        Returns:
            Raw PNG bytes of the composed preview image.
        """
        # Create canvas
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
        draw   = ImageDraw.Draw(canvas)

        # Map items into their category slots
        slot_map: Dict[str, Optional[Dict[str, Any]]] = {
            "TOPS":      None,
            "OUTERWEAR": None,
            "BOTTOMS":   None,
            "FOOTWEAR":  None,
        }

        for item in outfit_items:
            cat = cls._normalize_category(item)
            if cat in slot_map and slot_map[cat] is None:
                slot_map[cat] = item

        # Determine rendering order (OUTERWEAR replaces TOPS slot if present)
        render_order = []
        if slot_map["OUTERWEAR"]:
            render_order.append(("OUTERWEAR", slot_map["OUTERWEAR"]))
        elif slot_map["TOPS"]:
            render_order.append(("TOPS", slot_map["TOPS"]))
        if slot_map["BOTTOMS"]:
            render_order.append(("BOTTOMS", slot_map["BOTTOMS"]))
        if slot_map["FOOTWEAR"]:
            render_order.append(("FOOTWEAR", slot_map["FOOTWEAR"]))

        if not render_order:
            logger.warning("OutfitPreviewBuilder: No renderable garment slots found in outfit.")

        center_x = CANVAS_W // 2

        # Draw slot label strips for used slots
        for slot_key, item in render_order:
            _draw_slot_label_strip(draw, slot_key, CANVAS_W)

        # Paste each garment image
        for slot_key, item in render_order:
            image_path = cls._resolve_image_path(item)
            if image_path:
                _paste_garment(canvas, image_path, slot_key, center_x)
            else:
                logger.warning(f"OutfitPreviewBuilder: No image path for slot {slot_key}.")

        # Draw vertical separators between slots
        for sep_y in [520, 1050]:
            _draw_vertical_separator(draw, sep_y, CANVAS_W)

        # Overlay score badge
        _draw_score_badge(canvas, draw, score)

        # Draw footer
        _draw_footer(draw, occasion, season, reasoning)

        # Flatten to RGB for export (replaces transparent with BG dark colour)
        background = Image.new("RGB", canvas.size, (13, 14, 18))
        background.paste(canvas, mask=canvas.split()[3])   # use alpha channel as mask

        # Encode to PNG bytes
        buffer = io.BytesIO()
        background.save(buffer, format="PNG", optimize=True)
        raw_bytes = buffer.getvalue()

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(raw_bytes)
            logger.info(f"OutfitPreviewBuilder: Preview saved to {output_path}")

        return raw_bytes

    @staticmethod
    def _normalize_category(item: Dict[str, Any]) -> str:
        """
        Normalizes the item's category field to one of the standard slot keys.
        Handles both raw DB category strings and taxonomy-normalized strings.
        """
        from app.recommendation.rules.fashion_taxonomy import CATEGORY_MAP
        raw = str(item.get("category", "TOPS"))
        return CATEGORY_MAP.get(raw, raw.upper())

    @staticmethod
    def _resolve_image_path(item: Dict[str, Any]) -> Optional[str]:
        """
        Resolves the processed image file path from an outfit item dict.
        Supports both the recommendation engine dict format and the raw DB ORM format.
        """
        # Recommendation engine normalized dicts store an 'embedding_path';
        # look for 'processed_image_path' first (full DB dict injected from route)
        for key in ("processed_image_path", "image_path"):
            p = item.get(key)
            if p and Path(p).exists():
                return str(p)
        return None
