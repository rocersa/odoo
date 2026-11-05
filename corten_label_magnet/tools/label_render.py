"""Render the Corten magnet label to a print-ready PNG.

The label is drawn in its reading orientation (70 x 72 mm, or 120 x 72 mm with
a product image), then rotated to the paper's orientation (72 mm across the
roll, the length along the feed) because the Epson TM-m30III is fed the short
edge. Pure black on white: the printer is direct-thermal and prints one colour,
so a colour product image is rendered as a one-bit halftone.

The equivalent offline proofing tool is the root repo's `scripts/au-label.py`.
Geometry and type rules must stay identical; the constants below are the
contract.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

FONT_DIR = Path(__file__).resolve().parent.parent / "static" / "src" / "fonts"

LABEL_W_MM = 70.0        # default along-strip length (reading orientation)
LABEL_IMAGE_LENGTH_MM = 120.0  # image variant: image panel + text column
LABEL_H_MM = 72.0
MARGIN_MM = 3.0
MARGIN_MM_RIGHT = 3.0
BARCODE_H_MM = 14.0
HUMAN_H_MM = 4.4
HEADER_Y_MM = 4.5
QUIET_ZONE_MM = 1.6
MAX_MODULE_MM = 0.50
# Product barcodes are standardised to P<id> (8 chars, e.g. P0002823).
CODE_REF_CHARS = 8
# The code line stops growing here; 8 characters fill the width well before it.
CODE_MAX_CAP_MM = 7.0
MIN_MODULE_MM = 0.19      # ~1.5 dots at 203 dpi: below this a scan is unreliable
# Image variant: a square photo panel on the left, the type and barcode right.
IMAGE_W_MM = 50.0
IMAGE_H_MM = 50.0
IMAGE_Y_MM = 13.0
IMAGE_GAP_MM = 5.0
IMAGE_BORDER_MM = 0.3

INK = (0, 0, 0)
WHITE = (255, 255, 255)

# Code 128 symbol patterns, values 0-105 (stop is separate).
PATTERNS = (
    '11011001100', '11001101100', '11001100110', '10010011000',
    '10010001100', '10001001100', '10011001000', '10011000100',
    '10001100100', '11001001000', '11001000100', '11000100100',
    '10110011100', '10011011100', '10011001110', '10111001100',
    '10011101100', '10011100110', '11001110010', '11001011100',
    '11001001110', '11011100100', '11001110100', '11101101110',
    '11101001100', '11100101100', '11100100110', '11101100100',
    '11100110100', '11100110010', '11011011000', '11011000110',
    '11000110110', '10100011000', '10001011000', '10001000110',
    '10110001000', '10001101000', '10001100010', '11010001000',
    '11000101000', '11000100010', '10110111000', '10110001110',
    '10001101110', '10111011000', '10111000110', '10001110110',
    '11101110110', '11010001110', '11000101110', '11011101000',
    '11011100010', '11011101110', '11101011000', '11101000110',
    '11100010110', '11101101000', '11101100010', '11100011010',
    '11101111010', '11001000010', '11110001010', '10100110000',
    '10100001100', '10010110000', '10010000110', '10000101100',
    '10000100110', '10110010000', '10110000100', '10011010000',
    '10011000010', '10000110100', '10000110010', '11000010010',
    '11001010000', '11110111010', '11000010100', '10001111010',
    '10100111100', '10010111100', '10010011110', '10111100100',
    '10011110100', '10011110010', '11110100100', '11110010100',
    '11110010010', '11011011110', '11011110110', '11110110110',
    '10101111000', '10100011110', '10001011110', '10111101000',
    '10111100010', '11110101000', '11110100010', '10111011110',
    '10111101110', '11101011110', '11110101110', '11010000100',
    '11010010000', '11010011100',
)
STOP = "1100011101011"
START_B = 104


def _mm(dpi: float) -> float:
    return dpi / 25.4


def px(mm: float, dpi: float) -> int:
    return int(round(mm * _mm(dpi)))


def encode_code128b(data: str) -> str:
    """Return the module string (1 = bar) for a Code 128B symbol."""
    if not data:
        raise ValueError("barcode data is empty")
    values = []
    for ch in data:
        o = ord(ch)
        if not 32 <= o <= 126:
            raise ValueError(f"character {ch!r} is outside Code 128B printable ASCII")
        values.append(o - 32)
    checksum = (START_B + sum(v * i for i, v in enumerate(values, start=1))) % 103
    return "".join([PATTERNS[START_B], *[PATTERNS[v] for v in values],
                    PATTERNS[checksum], STOP])


def _font(name: str, cap_mm: float, dpi: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), max(1, int(cap_mm * _mm(dpi) * 1.45)))


def _tracked(draw, x, y, text, font, tracking_mm, dpi):
    tr = tracking_mm * _mm(dpi)
    for ch in text:
        draw.text((x, y), ch, font=font, fill=INK)
        x += draw.textlength(ch, font=font) + tr
    return x - tr


def _tracked_width(draw, text, font, tracking_mm, dpi):
    tr = tracking_mm * _mm(dpi)
    return sum(draw.textlength(c, font=font) for c in text) + max(0, len(text) - 1) * tr


def _cap_for_chars(draw, count, face, tracking_mm, max_w, dpi):
    """Cap height at which `count` monospace characters fill max_w exactly."""
    lo, hi = 1.0, 6.0
    while hi - lo > 0.01:
        mid = (lo + hi) / 2
        f = _font(face, mid, dpi)
        if _tracked_width(draw, "M" * count, f, tracking_mm, dpi) <= max_w:
            lo = mid
        else:
            hi = mid
    return lo


def _fit(draw, text, face, cap_mm, max_w, dpi):
    while cap_mm > 1.4:
        f = _font(face, cap_mm, dpi)
        if draw.textlength(text, font=f) <= max_w:
            return f
        cap_mm -= 0.1
    return _font(face, 1.4, dpi)


def _wrap_two(draw, name, face, cap_mm, max_w, dpi):
    """Split a product name across two lines, balanced and unit-aware.

    Prefer a split that does not separate a measurement from its unit or the
    multiplication sign, then the most even two lines at the largest size.
    """
    words = name.split()
    single = _fit(draw, name, face, cap_mm, max_w, dpi)
    candidates = []
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        fa = _fit(draw, a, face, cap_mm, max_w, dpi)
        fb = _fit(draw, b, face, cap_mm, max_w, dpi)
        common = min(fa.size, fb.size)
        wa = draw.textlength(a, font=fa)
        wb = draw.textlength(b, font=fb)
        nxt = words[i].lower()
        bad_boundary = nxt in ("x", "×") or bool(re.fullmatch(r"[\d.,]+", words[i - 1]))
        candidates.append((common, abs(wa - wb), bad_boundary, a, b))
    if candidates:
        max_common = max(c[0] for c in candidates)
        viable = [c for c in candidates if c[0] >= max_common * 0.92]
        viable.sort(key=lambda c: (c[2], c[1]))
        best = viable[0]
        if best[0] > single.size:
            f = ImageFont.truetype(str(FONT_DIR / face), best[0])
            return [best[3], best[4]], [f, f]
    return [name], [single]


def barcode_fits(data: str, width_mm: float | None = None) -> bool:
    if width_mm is None:
        width_mm = LABEL_W_MM - MARGIN_MM - MARGIN_MM_RIGHT
    """False when the payload would need a module narrower than a reliable scan."""
    modules = len(encode_code128b(data))
    usable_mm = width_mm - 2 * QUIET_ZONE_MM
    return usable_mm / modules >= MIN_MODULE_MM


def _barcode(draw, data, x_mm, y_mm, w_mm, h_mm, dpi):
    modules = encode_code128b(data)
    usable = px(w_mm, dpi) - px(2 * QUIET_ZONE_MM, dpi)
    unit = min(MAX_MODULE_MM * _mm(dpi), usable / len(modules))
    bars_w = unit * len(modules)
    x0 = px(x_mm, dpi) + (px(w_mm, dpi) - bars_w) / 2
    y0, y1 = px(y_mm, dpi), px(y_mm + h_mm, dpi)
    for i, m in enumerate(modules):
        if m == "1":
            draw.rectangle([x0 + round(i * unit), y0, x0 + round((i + 1) * unit), y1],
                           fill=INK)


def derive_location(code: str):
    """Split a location path into (small line, big line).

    Only "/" separates path segments, so a leaf name may contain spaces
    ("Unit 1"). The parent path (without the warehouse root) is the small line
    above the leaf; the leaf is the big line.
    """
    parts = [p for p in code.strip().split("/") if p]
    if not parts:
        return "", code
    return " / ".join(parts[1:-1]), parts[-1]


def prepare_image(data, w_mm, h_mm, dpi):
    """Fit a product image into the panel as a one-bit thermal halftone.

    Colour product photos are flattened onto white, autocontrasted and
    dithered to black/white: a direct-thermal head has no grey level, so the
    dot pattern carries the tone. Raising ValueError lets the report drop the
    image and still print the label rather than failing the whole run.
    """
    if not data:
        raise ValueError("image data is empty")
    try:
        src = Image.open(io.BytesIO(data))
        src.load()
    except Exception as exc:  # Pillow raises a dozen parser errors
        raise ValueError(f"image could not be read: {exc}") from exc
    if src.mode in ("RGBA", "LA", "P"):
        src = src.convert("RGBA")
        plate = Image.new("RGBA", src.size, (255, 255, 255, 255))
        src = Image.alpha_composite(plate, src)
    src = src.convert("L")
    src = ImageOps.autocontrast(src, cutoff=0.5)
    target = (px(w_mm, dpi), px(h_mm, dpi))
    src.thumbnail(target, Image.LANCZOS)
    canvas = Image.new("L", target, 255)
    canvas.paste(src, ((target[0] - src.width) // 2, (target[1] - src.height) // 2))
    return canvas.convert("1", dither=Image.Dither.FLOYDSTEINBERG).convert("RGB")


def draw_label(kind, code, dpi, *, name=None, detail=None, length_mm=LABEL_W_MM,
               image=None):
    W, H = px(length_mm, dpi), px(LABEL_H_MM, dpi)
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    m = px(MARGIN_MM, dpi)
    right = W - px(MARGIN_MM_RIGHT, dpi)
    content_w = right - m

    # The image variant gives the left of the label to the photo and sets the
    # type in a narrower column beside it.
    tx, text_w = m, content_w
    with_image = kind == "product" and image is not None
    if with_image:
        x_mm = MARGIN_MM
        panel = prepare_image(image, IMAGE_W_MM, IMAGE_H_MM, dpi)
        img.paste(panel, (px(x_mm, dpi), px(IMAGE_Y_MM, dpi)))
        border = max(1, px(IMAGE_BORDER_MM, dpi))
        x0, y0 = px(x_mm, dpi), px(IMAGE_Y_MM, dpi)
        x1, y1 = x0 + px(IMAGE_W_MM, dpi), y0 + px(IMAGE_H_MM, dpi)
        d.rectangle([x0, y0, x1, y1], outline=INK, width=border)
        tx = px(MARGIN_MM + IMAGE_W_MM + IMAGE_GAP_MM, dpi)
        text_w = right - tx

    kick = _font("Archivo-700.ttf", 2.2, dpi)
    _tracked(d, m, px(HEADER_Y_MM, dpi), "COR-TEN-STEEL", kick, 0.16, dpi)
    tag_txt = "AU · LOCATION" if kind == "location" else "AU · PRODUCT"
    tag = _font("IBMPlexMono-600.ttf", 1.9, dpi)
    tw = _tracked_width(d, tag_txt, tag, 0.10, dpi)
    _tracked(d, right - tw, px(HEADER_Y_MM + 0.2, dpi), tag_txt, tag, 0.10, dpi)

    if kind == "location":
        # The big lines are the location's address; the barcode payload may be
        # a different string, so never derive the name from it.
        top, big = derive_location(detail or code)
        if top:
            ftop = _fit(d, top, "IBMPlexMono-600.ttf", 4.2, content_w, dpi)
            d.text((m, px(13.4, dpi)), top, font=ftop, fill=INK)
            big_y = 20.2
        else:
            big_y = 17.0
        fbig = _fit(d, big, "IBMPlexMono-700.ttf", 13.0, content_w, dpi)
        d.text((m - px(0.3, dpi), px(big_y, dpi)), big, font=fbig, fill=INK)
    else:
        lines, fonts = _wrap_two(d, name or "", "Archivo-900.ttf", 6.3, text_w, dpi)
        for i, (line, f) in enumerate(zip(lines, fonts)):
            d.text((tx, px(13.2 + i * 7.4, dpi)), line, font=f, fill=INK)
        if detail:
            # One size for every product code: the longest code in stock fills
            # the label width, so shorter codes are as large as they can be
            # without a per-label size change.
            code_cap = min(CODE_MAX_CAP_MM,
                           _cap_for_chars(d, CODE_REF_CHARS, "IBMPlexMono-600.ttf",
                                          0.11, text_w, dpi))
            fdet = _fit(d, detail, "IBMPlexMono-600.ttf", code_cap, text_w, dpi)
            _tracked(d, tx, px(32.4, dpi), detail, fdet, 0.08, dpi)

    if code:
        if barcode_fits(code, text_w / _mm(dpi)):
            by = H - px(MARGIN_MM, dpi) - px(HUMAN_H_MM, dpi) - px(BARCODE_H_MM, dpi)
            _barcode(d, code, tx / _mm(dpi), by * 25.4 / dpi,
                     text_w / _mm(dpi), BARCODE_H_MM, dpi)
        # Under the barcode the code stays a secondary read: cap it so it
        # clears the bottom margin on the wide label, and anchor its ink to
        # the margin rather than a fixed offset.
        human_cap = 2.4
        if kind != "location" and detail:
            human_cap = min(3.0, _cap_for_chars(d, CODE_REF_CHARS,
                                                "IBMPlexMono-600.ttf", 0.11,
                                                text_w, dpi))
        human = _fit(d, code, "IBMPlexMono-600.ttf", human_cap, text_w, dpi)
        hw = _tracked_width(d, code, human, 0.11, dpi)
        bbox = d.textbbox((0, 0), code, font=human)
        bottom = H - px(MARGIN_MM, dpi) - px(0.3, dpi)
        _tracked(d, tx + (text_w - hw) / 2, bottom - bbox[3], code, human, 0.11, dpi)
    return img


def render_png(kind, code, *, name=None, detail=None, dpi=600,
               length_mm=LABEL_W_MM, image=None, mono=False) -> bytes:
    """Return the rotated, print-oriented PNG bytes for one label.

    `mono` thresholds the artwork to one bit instead of leaving the type
    antialiased. The printer is one-bit, and dithering antialiased type is what
    makes it look fuzzy; the photo panel is already halftoned, so a threshold
    leaves it alone.
    """
    try:
        img = draw_label(kind, code, dpi, name=name, detail=detail,
                         length_mm=length_mm, image=image)
    except ValueError:
        if image is None:
            raise
        # An unreadable photo must not cost the label its barcode: retry
        # without the panel.
        img = draw_label(kind, code, dpi, name=name, detail=detail,
                         length_mm=length_mm)
    rotated = img.rotate(-90, expand=True)
    if mono:
        rotated = (rotated.convert("L")
                   .point(lambda v: 255 if v >= 128 else 0)
                   .convert("1", dither=Image.Dither.NONE))
    buf = io.BytesIO()
    rotated.save(buf, format="PNG", dpi=(dpi, dpi))
    return buf.getvalue()
