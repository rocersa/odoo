# Copyright 2019 Tecnativa - Sergio Teruel
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class ProductAttributeValues(WebsiteSale):
    def _get_additional_shop_values(self, values, **kwargs):
        res = super()._get_additional_shop_values(values, **kwargs)
        attributes = values.get("attributes")
        if attributes:
            # Get products to use for determining available filter options.
            # Use search_domain (before attribute filtering) if available, 
            # otherwise get all published products to ensure filter options
            # are based on all products on the page before any filters are selected.
            search_domain = values.get("search_domain")
            base_products = None
            
            if search_domain is not None:
                # Use the base search domain (excludes attribute value filters)
                base_products = request.env["product.template"].search(search_domain)
            else:
                # Fallback: Get search_product from parent, which should work
                # if search_domain isn't available
                base_products = values.get("search_product")
            
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
