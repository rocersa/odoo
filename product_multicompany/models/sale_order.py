# -*- coding: utf-8 -*-

from odoo import models
from odoo.fields import Domain


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_product_catalog_domain(self):
        return (
            Domain('company_ids', '=', False)
            | Domain('company_ids', 'in', self.env.companies.ids)
        ) & Domain('type', '!=', 'combo') & Domain('sale_ok', '=', True)
