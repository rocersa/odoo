from odoo import models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _get_applicable_rules(self, products, quantity, date, *, uom=None, **kwargs):
        """Override to sort area-filter rules before plain template rules.

        Rules with area filters are more specific and should be evaluated
        first within the same applied_on level.
        """
        rules = super()._get_applicable_rules(
            products, quantity, date, uom=uom, **kwargs)
        return rules.sorted(
            key=lambda r: (r.applied_on, not r.has_area_filter),
        )
