import re

from odoo import _, api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    custom_name = fields.Char(
        string="Rule Name",
        help="Optional label for this pricelist rule. "
             "Overrides the auto-generated 'Applied On' name.",
    )

    min_area = fields.Float(
        string="Min Area (mm²)",
        help="Minimum variant area (Long Edge × Short Edge) in mm² for this "
             "rule to apply. Leave 0 to ignore.",
    )
    max_area = fields.Float(
        string="Max Area (mm²)",
        help="Maximum variant area (Long Edge × Short Edge) in mm² for this "
             "rule to apply. Leave 0 to ignore.",
    )

    has_area_filter = fields.Boolean(
        compute='_compute_has_area_filter',
        store=True,
    )

    @api.depends('min_area', 'max_area')
    def _compute_has_area_filter(self):
        for item in self:
            item.has_area_filter = bool(item.min_area or item.max_area)

    @api.depends('applied_on', 'categ_id', 'product_tmpl_id', 'product_id',
                 'custom_name')
    def _compute_name(self):
        for item in self:
            if item.custom_name:
                item.name = item.custom_name
            else:
                super(ProductPricelistItem, item)._compute_name()

    def _is_applicable_for(self, product, qty_in_product_uom):
        """Extend to check area filter on template-level rules."""
        res = super()._is_applicable_for(product, qty_in_product_uom)
        if not res or not self.has_area_filter:
            return res

        # Resolve to product.product if possible
        if product._name == 'product.template':
            if product.product_variant_count == 1:
                product = product.product_variant_id
            else:
                return False

        area = self._get_variant_area(product)
        if area is None:
            return False

        if self.min_area and area < self.min_area:
            return False
        if self.max_area and area > self.max_area:
            return False

        return True

    def _get_variant_area(self, product):
        """Compute panel area from variant attribute values.

        Looks for two numeric mm attributes on the variant (e.g.
        "Long Edge: 1500 mm", "Short Edge: 600 mm") and returns their product.
        Returns None if two numeric dimensions cannot be found.
        """
        dims = []
        for ptav in product.product_template_attribute_value_ids:
            val_name = ptav.product_attribute_value_id.name or ''
            match = re.match(r'^(\d+(?:\.\d+)?)\s*mm$', val_name.strip())
            if match:
                dims.append(float(match.group(1)))
        if len(dims) >= 2:
            # Use the two largest dimensions (handles 3-dimension products)
            dims.sort(reverse=True)
            return dims[0] * dims[1]
        return None
