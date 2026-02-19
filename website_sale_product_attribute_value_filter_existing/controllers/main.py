# Copyright 2019 Tecnativa - Sergio Teruel
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class ProductAttributeValues(WebsiteSale):
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, tags='', **post):
        """Override shop to get base products (without attribute filters) for filter options."""
        # Get the base domain without attribute filters to determine available filter values
        # This ensures filter options stay consistent across all products on the page
        base_domain = self._get_shop_domain(
            search=search,
            category=category,
            attribute_value_dict={},  # No attribute filters
        )
        
        # Store in session/post so _get_additional_shop_values can access it
        post['_base_domain'] = base_domain
        
        return super().shop(page=page, category=category, search=search, min_price=min_price, max_price=max_price, tags=tags, **post)

    def _get_additional_shop_values(self, values, **kwargs):
        res = super()._get_additional_shop_values(values, **kwargs)
        attributes = values.get("attributes")
        
        if attributes:
            # Get base products using the base domain (without attribute filters)
            # This ensures that available filter options are based on all products
            # on the page before any filters are selected
            base_domain = kwargs.get('_base_domain')
            base_products = None
            
            if base_domain is not None:
                base_products = request.env["product.template"].search(base_domain)
            
            if base_products:
                ProductTemplateAttributeLine = request.env[
                    "product.template.attribute.line"
                ]
                lines = ProductTemplateAttributeLine.search_read(
                    domain=[
                        ("product_tmpl_id", "in", base_products.ids),
                        ("attribute_id", "in", attributes.ids),
                        ("attribute_id.visibility", "=", "visible"),
                    ],
                    fields=["value_ids"],
                )
                used_value_ids = {
                    value_id for line in lines for value_id in line.get("value_ids", [])
                }
                res["attr_values_used_ids"] = used_value_ids
        return res
