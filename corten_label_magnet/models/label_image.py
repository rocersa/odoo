"""Shared compute for the label image field, so every model renders the same way."""
from __future__ import annotations

import base64
import logging

from odoo import api, models

from ..tools.label_render import render_png

_logger = logging.getLogger(__name__)


def label_image(kind, name, code, detail=None):
    """PNG bytes for one label, with a readable failure instead of a traceback."""
    try:
        return render_png(kind, code, name=name, detail=detail, dpi=600)
    except ValueError as exc:
        _logger.warning("Magnet label skipped the barcode for %r: %s", code, exc)
        return render_png(kind, "", name=name, detail=detail, dpi=600)


class CortenLabelImage(models.AbstractModel):
    _name = "corten.label.image"
    _description = "Magnet label image helper"

    @api.model
    def get_label_image(self, kind, name, code, detail=None):
        # Odoo 19 Binary fields hold the base64 payload as bytes (a str is
        # encoded on assignment); QWeb's image_data_uri() expects that form.
        return base64.b64encode(label_image(kind, name, code, detail)).decode("ascii")
