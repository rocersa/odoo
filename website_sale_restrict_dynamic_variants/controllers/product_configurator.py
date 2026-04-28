from odoo import http, _
from odoo.exceptions import UserError

from odoo.addons.sale.controllers.product_configurator import SaleProductConfiguratorController


class RestrictProductConfiguratorController(SaleProductConfiguratorController):

    @http.route(
        route='/sale/product_configurator/create_product',
        type='jsonrpc',
        auth='user',
        methods=['POST'],
    )
    def sale_product_configurator_create_product(self, product_template_id, ptav_ids):
        """Block implicit variant creation in the backend product configurator."""
        product_template = self._get_product_template(product_template_id)
        if product_template.restrict_dynamic_variants:
            combination = request.env['product.template.attribute.value'].browse(ptav_ids)
            variant = product_template._get_variant_for_combination(combination)
            if not variant:
                raise UserError(_(
                    "This product is restricted to existing variants only. "
                    "The selected combination does not exist."
                ))
            if not variant.active:
                raise UserError(_(
                    "This product is restricted to existing variants only. "
                    "The selected combination has been archived."
                ))
            return variant.id
        return super().sale_product_configurator_create_product(product_template_id, ptav_ids)
