from odoo import models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _get_applicable_rules(self, products, date, **kwargs):
        """Override to sort attribute-filter rules before plain template rules.

        Rules with attribute filters are more specific and should be evaluated
        first within the same applied_on level.
        """
        rules = super()._get_applicable_rules(products, date, **kwargs)
        # Stable sort: filtered rules first (has_attribute_filter=True sorts
        # before False when reversed), preserving original order within groups.
        return rules.sorted(
            key=lambda r: (r.applied_on, not r.has_attribute_filter),
        )
