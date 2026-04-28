# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    company_ids = fields.Many2many(
        'res.company', string='Companies',
        relation='product_template_res_company_rel',
        help="Leave empty to share with all companies."
    )

    company_id = fields.Many2one(
        'res.company', string='Company',
        compute='_compute_company_id',
        inverse='_inverse_company_id',
        store=True,
        readonly=False,
        index=True,
    )

    @api.depends('company_ids')
    def _compute_company_id(self):
        for product in self:
            if len(product.company_ids) == 1:
                product.company_id = product.company_ids.id
            else:
                product.company_id = False

    def _inverse_company_id(self):
        for product in self:
            if product.company_id:
                product.company_ids = [(6, 0, [product.company_id.id])]
            else:
                product.company_ids = [(5,)]

    @api.model
    def _check_company_domain(self, companies):
        return ['|', ('company_ids', '=', False), ('company_ids', 'in', companies.ids)]
