"""Report models: render the label images the QWeb templates embed.

Rendering lives here, not in computed fields, because the label length is a
choice made in the Print Labels wizard (70 mm, 100 mm, or 120 mm with the
product image).
"""
from __future__ import annotations

import base64
import logging

from odoo import models

from ..tools.label_render import LABEL_IMAGE_LENGTH_MM, render_png

_logger = logging.getLogger(__name__)

LENGTH_STANDARD = 70.0
LENGTH_WIDE = 100.0
LENGTH_IMAGE = LABEL_IMAGE_LENGTH_MM


def _label_fields(record):
    """(kind, name, barcode value, detail line) for one record."""
    if record._name == "product.product":
        return ("product", record.display_name,
                record.barcode or record.default_code or "", record.default_code)
    if record._name == "product.template":
        return ("product", record.name,
                record.barcode or record.default_code or "", record.default_code)
    return ("location", record.name,
            record.barcode or record.complete_name or "",
            record.complete_name or record.name)


def _product_image(record):
    """Raw bytes of the product photo, or None when the product has none.

    The 1024 px size is ample for the 50 mm panel at 203 dpi and keeps the
    report memory small. The image is optional: no photo still prints a label.
    """
    if record._name not in ("product.product", "product.template"):
        return None
    value = (getattr(record, "image_1024", False)
             or getattr(record, "image_512", False)
             or getattr(record, "image_1920", False))
    if not value:
        return None
    try:
        return base64.b64decode(value)
    except (TypeError, ValueError):
        return None


def label_values(env, docids, data, length_mm, with_image=False):
    data = data or {}
    quantities = data.get("quantity_by_product") or {}
    active_model = data.get("active_model")

    if active_model in ("product.template", "product.product") and quantities:
        docs = env[active_model].browse([int(p) for p in quantities]).exists()
        copies = {int(p): max(int(q), 1) for p, q in quantities.items()}
    else:
        docs = env["stock.location"].browse(docids or []).exists()
        copies = {rec.id: 1 for rec in docs}

    labels = {}
    for record in docs:
        kind, name, code, detail = _label_fields(record)
        image = _product_image(record) if with_image and kind == "product" else None
        try:
            png = render_png(kind, code, name=name, detail=detail,
                             dpi=203.2, length_mm=length_mm, image=image,
                             mono=True)
        except ValueError as exc:
            # A barcode value outside printable ASCII: still print the label,
            # without bars, rather than fail the whole run.
            _logger.warning("Magnet label dropped the barcode for %r: %s", code, exc)
            png = render_png(kind, "", name=name, detail=detail,
                             dpi=203.2, length_mm=length_mm, image=image,
                             mono=True)
        labels[record.id] = base64.b64encode(png)

    return {
        "docs": docs,
        "copies": copies,
        "labels": labels,
        # the page's feed length; the template insets by 0.5 mm
        "page_h": int(round(length_mm)),
    }


class ReportCortenLabel(models.AbstractModel):
    _name = "report.corten_label_magnet.report_label"
    _description = "Magnet label (72 x 70 mm)"

    def _get_report_values(self, docids, data):
        return label_values(self.env, docids, data, LENGTH_STANDARD)


class ReportCortenLabelWide(models.AbstractModel):
    _name = "report.corten_label_magnet.report_label_100"
    _description = "Magnet label (72 x 100 mm)"

    def _get_report_values(self, docids, data):
        return label_values(self.env, docids, data, LENGTH_WIDE)


class ReportCortenLabelImage(models.AbstractModel):
    _name = "report.corten_label_magnet.report_label_image"
    _description = "Magnet label with image (72 x 120 mm)"

    def _get_report_values(self, docids, data):
        return label_values(self.env, docids, data, LENGTH_IMAGE, with_image=True)
