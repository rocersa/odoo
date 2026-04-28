from odoo import http, _
from odoo.exceptions import UserError

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleRestrictDynamicVariants(WebsiteSale):

    def _prepare_product_values(self, product, category, **kwargs):
        """Pass visible ptav ids to the template so unavailable options can be hidden."""
        vals = super()._prepare_product_values(product, category, **kwargs)
        if product.restrict_dynamic_variants:
            visible_ptavs = set()
            for variant in product._get_visible_variants():
                visible_ptavs.update(variant.product_template_attribute_value_ids.ids)
            vals['visible_ptav_ids'] = list(visible_ptavs)
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info(
                "Product %s (id=%s): prepared %d visible ptavs for template",
                product.name, product.id, len(visible_ptavs),
            )
        return vals

    @http.route(
        ['/shop/product/media/update'],
        type='jsonrpc',
        auth='user',
        methods=['POST'],
        website=True,
    )
    def product_media_update(self, product_template_id, product_product_id, media_type,
                             media_data, combination_ids=None):
        """Prevent media updates from implicitly creating a missing variant."""
        product_template = request.env['product.template'].browse(int(product_template_id))
        if product_template.restrict_dynamic_variants and combination_ids:
            combination = request.env['product.template.attribute.value'].browse(combination_ids)
            product_product = product_template._get_variant_for_combination(combination)
            if not product_product:
                raise UserError(_(
                    "Cannot update media for a combination that does not exist. "
                    "Create the variant first, or disable 'Restrict to Existing Variants'."
                ))
        return super().product_media_update(
            product_template_id, product_product_id, media_type, media_data,
            combination_ids=combination_ids,
        )
