# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    company_ids = fields.Many2many(
        'res.company',
        relation='product_template_res_company_rel',
        string='Catalogs',
        help="Show this product in the listed companies' product catalogs only. "
             "Leave empty to show in every company's catalog.",
    )
