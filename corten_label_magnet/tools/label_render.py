"""Render the Corten magnet label to a print-ready PNG.

The label is drawn in its reading orientation at 70 x 72 mm, then rotated to
the paper's orientation (72 mm across the roll, 70 mm along the feed) because
the Epson TM-m30III is fed the short edge. Pure black on white: the printer is
direct-thermal and prints one colour.

The equivalent offline proofing tool is the root repo's `scripts/au-label.py`.
Geometry and type rules must stay identical; the constants below are the
contract.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(__file__).resolve().parent.parent / "static" / "src" / "fonts"

LABEL_W_MM = 70.0        # default along-strip length (reading orientation)
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


RACK_LEAF = re.compile(r"^[A-Za-z]\d+-L\d+$")


def derive_location(code: str):
    """Split a location path into (small line, big line).

    Only "/" separates path segments: the leaf name may itself contain spaces
    ("Unit 1"). The small line is only used for a rack address, where the
    parent segments identify the run; a plain leaf shows its name alone.
    """
    parts = [p for p in code.strip().split("/") if p]
    if not parts:
        return "", code
    big = parts[-1]
    if len(parts) >= 3 and RACK_LEAF.match(big):
        return " / ".join(parts[1:-1]), big
    return "", big


def draw_label(kind, code, dpi, *, name=None, detail=None, length_mm=LABEL_W_MM):
    W, H = px(length_mm, dpi), px(LABEL_H_MM, dpi)
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    m = px(MARGIN_MM, dpi)
    right = W - px(MARGIN_MM_RIGHT, dpi)
    content_w = right - m

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
        lines, fonts = _wrap_two(d, name or "", "Archivo-900.ttf", 6.3, content_w, dpi)
        for i, (line, f) in enumerate(zip(lines, fonts)):
            d.text((m, px(13.2 + i * 7.4, dpi)), line, font=f, fill=INK)
        if detail:
            # One size for every product code: the longest code in stock fills
            # the label width, so shorter codes are as large as they can be
            # without a per-label size change.
            code_cap = min(CODE_MAX_CAP_MM,
                           _cap_for_chars(d, CODE_REF_CHARS, "IBMPlexMono-600.ttf",
                                          0.11, content_w, dpi))
            fdet = _fit(d, detail, "IBMPlexMono-600.ttf", code_cap, content_w, dpi)
            _tracked(d, m, px(32.4, dpi), detail, fdet, 0.08, dpi)

    if code:
        if barcode_fits(code, length_mm - MARGIN_MM - MARGIN_MM_RIGHT):
            by = H - px(MARGIN_MM, dpi) - px(HUMAN_H_MM, dpi) - px(BARCODE_H_MM, dpi)
            _barcode(d, code, MARGIN_MM, by * 25.4 / dpi,
                     length_mm - MARGIN_MM - MARGIN_MM_RIGHT, BARCODE_H_MM, dpi)
        # Under the barcode the code stays a secondary read: cap it so it
        # clears the bottom margin on the wide label, and anchor its ink to
        # the margin rather than a fixed offset.
        human_cap = 2.4
        if kind != "location" and detail:
            human_cap = min(3.0, _cap_for_chars(d, CODE_REF_CHARS,
                                                "IBMPlexMono-600.ttf", 0.11,
                                                content_w, dpi))
        human = _fit(d, code, "IBMPlexMono-600.ttf", human_cap, content_w, dpi)
        hw = _tracked_width(d, code, human, 0.11, dpi)
        bbox = d.textbbox((0, 0), code, font=human)
        bottom = H - px(MARGIN_MM, dpi) - px(0.3, dpi)
        _tracked(d, (W - hw) / 2, bottom - bbox[3], code, human, 0.11, dpi)
    return img


def render_png(kind, code, *, name=None, detail=None, dpi=600,
               length_mm=LABEL_W_MM) -> bytes:
    """Return the rotated, print-oriented PNG bytes for one label."""
    img = draw_label(kind, code, dpi, name=name, detail=detail, length_mm=length_mm)
    rotated = img.rotate(-90, expand=True)
    buf = io.BytesIO()
    rotated.save(buf, format="PNG", dpi=(dpi, dpi))
    return buf.getvalue()
