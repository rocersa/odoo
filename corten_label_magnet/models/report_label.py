"""Report models: render the label images the QWeb templates embed.

Rendering lives here, not in computed fields, because the label length is a
choice made in the Print Labels wizard (70 mm or 100 mm along the strip).
"""
from __future__ import annotations

import base64
import logging

from odoo import models

from ..tools.label_render import render_png

_logger = logging.getLogger(__name__)

LENGTH_STANDARD = 70.0
LENGTH_WIDE = 100.0


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


def label_values(env, docids, data, length_mm):
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
        try:
            png = render_png(kind, code, name=name, detail=detail,
                             dpi=600, length_mm=length_mm)
        except ValueError as exc:
            # A barcode value outside printable ASCII: still print the label,
            # without bars, rather than fail the whole run.
            _logger.warning("Magnet label dropped the barcode for %r: %s", code, exc)
            png = render_png(kind, "", name=name, detail=detail,
                             dpi=600, length_mm=length_mm)
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
