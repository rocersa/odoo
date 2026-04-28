# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    company_ids = fields.Many2many(
        'res.company', string='Companies',
        related='product_tmpl_id.company_ids',
        readonly=False,
    )

    @api.model
    def _check_company_domain(self, companies):
        return ['|', ('company_ids', '=', False), ('company_ids', 'in', companies.ids)]
