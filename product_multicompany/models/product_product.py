# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.fields import Domain


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
        if not companies:
            return Domain('company_ids', '=', False)
        if isinstance(companies, str):
            company_ids = companies
        else:
            company_ids = models.to_record_ids(companies)
        return Domain([
            '|',
            '|', ('company_ids', '=', False), ('company_ids', 'in', company_ids),
            '&', ('company_ids', '=', False),
                 '|', ('product_tmpl_id.company_ids', '=', False), ('product_tmpl_id.company_ids', 'in', company_ids)
        ])
