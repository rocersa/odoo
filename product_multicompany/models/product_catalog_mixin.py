# -*- coding: utf-8 -*-

from odoo import models
from odoo.fields import Domain


class ProductCatalogMixin(models.AbstractModel):
    _inherit = 'product.catalog.mixin'

    def _get_product_catalog_domain(self):
        domain = super()._get_product_catalog_domain()
        if not self.company_id:
            return domain
        return domain & (
            Domain('product_tmpl_id.company_ids', '=', False)
            | Domain('product_tmpl_id.company_ids', 'in', self.company_id.ids)
        )
