# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.fields import Domain
from odoo.tools.misc import unquote


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

    def _get_attribute_exclusions(
        self, parent_combination=None, parent_name=None, combination_ids=None
    ):
        result = super()._get_attribute_exclusions(
            parent_combination=parent_combination,
            parent_name=parent_name,
            combination_ids=combination_ids,
        )
        # Hide combinations whose variant is restricted by company for the
        # current user.  We compare the full set of variants (sudo) with the
        # accessible set (respects ir.rule) to find restricted ones.
        all_variants = self.sudo().product_variant_ids
        accessible_variants = self.product_variant_ids
        restricted_variants = all_variants - accessible_variants
        if restricted_variants:
            restricted_combinations = [
                tuple(product.product_template_attribute_value_ids.ids)
                for product in restricted_variants
                if product.product_template_attribute_value_ids
            ]
            if restricted_combinations:
                archived = set(
                    tuple(c) for c in result.get('archived_combinations', [])
                )
                archived.update(restricted_combinations)
                result['archived_combinations'] = list(archived)
        return result

    @api.model
    def _check_company_domain(self, companies):
        if not companies:
            return Domain('company_ids', '=', False)
        if isinstance(companies, unquote):
            return Domain('company_ids', 'in', unquote(f'{companies} + [False]'))
        return Domain('company_ids', 'in', models.to_record_ids(companies) + [False])
