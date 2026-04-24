# -*- coding: utf-8 -*-
# Copyright 2024 Sveltware Solutions

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    public_website_ids = fields.Many2many(
        string='Websites (Variant)',
        comodel_name='website',
        relation='product_product_public_website_rel',
        column1='product_id',
        column2='website_id',
        help="If left blank, the variant inherits the template's website restriction.",
    )

    def _get_effective_website_restrictions(self):
        """Return the restriction set that applies to this variant.

        Fallback chain:
        1. Variant's own public_website_ids (if set)
        2. Template's public_website_ids | website_id
        3. Empty → visible everywhere
        """
        self.ensure_one()
        if self.public_website_ids:
            return self.public_website_ids
        tmpl = self.product_tmpl_id
        return tmpl.public_website_ids | tmpl.website_id

    def is_visible_on_current_website(self):
        website = self.env['website'].get_current_website()
        restricts = self._get_effective_website_restrictions()
        return not restricts or website.id in restricts.ids
