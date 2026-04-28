# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    company_ids = fields.Many2many(
        'res.company', string='Companies',
        relation='product_product_res_company_rel',
        help="If left blank, the variant inherits the template's company restriction.",
    )

    def _get_effective_company_ids(self):
        """Return the company restriction that applies to this variant.

        Fallback chain:
        1. Variant's own company_ids (if set)
        2. Template's company_ids
        3. Empty → visible to all companies
        """
        self.ensure_one()
        if self.company_ids:
            return self.company_ids
        return self.product_tmpl_id.company_ids

    @api.model
    def _check_company_domain(self, companies):
        return [
            '|',
            '|', ('company_ids', '=', False), ('company_ids', 'in', companies.ids),
            '&', ('company_ids', '=', False),
                 '|', ('product_tmpl_id.company_ids', '=', False), ('product_tmpl_id.company_ids', 'in', companies.ids)
        ]
