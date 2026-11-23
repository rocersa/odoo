import math
import re

from odoo import models

# The two panel-margin categories that hold the S00299 kitset panels. The
# storefront's `update_retail_cost()` proxies a non-standard length to the next
# standard length the catalogue sells on every Gabions product; the Odoo quote
# must mirror that rule here so the two bases agree.
PANEL_CATEGORY_NAMES = frozenset({
    "gabion panel margin 1 custom",
    "gabion panel margin 2 custom",
})

# A Gabion panel code: gauge prefix and two dimensions in mm, e.g.
# `Gab4.5-1275-450`. Case-insensitive because the catalogue also carries
# lower-case `gab3-…` / `gab4.5-…` duplicates.
PANEL_CODE_RE = re.compile(r"^(Gab[\d.]+)-(\d+)-(\d+)$", re.IGNORECASE)
GAUGE_RE = re.compile(r"^gab", re.IGNORECASE)

# Both dimensions in mm, gauge in mm; returns kg. This is the exact expression
# `update_retail_cost()` uses for `group = 'Gabions'`.
WIRE_DENSITY = 7.85
WEIGHT_SCALE = 1e-6


def panel_weight(height, width, gauge):
    span = height * (width / 75 + 1) + width * (height / 75 + 1)
    wire = math.pi * (gauge / 2) ** 2 * WIRE_DENSITY
    return span * wire * WEIGHT_SCALE


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _compute_base_price(self, product, quantity, uom, date, currency, **kwargs):
        price = super()._compute_base_price(
            product, quantity, uom, date, currency, **kwargs
        )
        if self.base != "standard_price":
            return price

        ratio = self._gabion_panel_proxy_ratio(product)
        if ratio is None:
            return price
        return price * ratio

    def _gabion_panel_proxy_ratio(self, product):
        """Weight ratio that turns a true-dimension cost into its proxy cost.

        Returns None when the product is not a proxied Gabion panel, so the
        caller falls through to the normal base price.
        """
        code = product.default_code or ""
        match = PANEL_CODE_RE.match(code)
        if not match:
            return None

        categ = product.categ_id
        if (categ.name or "").strip().lower() not in PANEL_CATEGORY_NAMES:
            return None

        gauge = GAUGE_RE.sub("", match.group(1))
        try:
            gauge = float(gauge)
            height, width = int(match.group(2)), int(match.group(3))
        except ValueError:
            return None
        if gauge <= 0 or height <= 0 or width <= 0:
            return None

        proxy = self._gabion_panel_proxy_lengths(height, width)
        proxy_height, proxy_width = proxy.get(height, height), proxy.get(width, width)
        if proxy_height == height and proxy_width == width:
            return None

        true_weight = panel_weight(height, width, gauge)
        if true_weight <= 0:
            return None
        return panel_weight(proxy_height, proxy_width, gauge) / true_weight

    def _gabion_panel_proxy_lengths(self, height, width):
        rows = self.env["gabion.panel.override"].sudo().search_read(
            [("current_length", "in", (height, width))],
            ["current_length", "proxy_length"],
        )
        return {row["current_length"]: row["proxy_length"] for row in rows}
