# -*- coding: utf-8 -*-

from odoo import models
from odoo.fields import Domain


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_product_catalog_domain(self):
        return (
            Domain('company_ids', '=', False)
            | Domain('company_ids', 'in', self.env.companies.ids)
        ) & Domain('type', '!=', 'combo') & Domain('purchase_ok', '=', True)
