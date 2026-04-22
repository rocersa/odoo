# -*- coding: utf-8 -*-
# Copyright 2024 Sveltware Solutions

from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class MultiWebsiteSale(WebsiteSale):
    def _get_additional_shop_values(self, values, **kwargs):
        """
        Limit only the specified websites can see eCommerce category.

        Ref#1: odoo/addons/website_sale/controllers/main.py
            Trace line: 273 -> 420 -> 468 -> 486
        Ref#2: odoo/addons/website_sale/views/templates.xml
            Trace line: 323 - 372 -> 645 -> 830
        """
        vals = super()._get_additional_shop_values(values, **kwargs)
        website = request.env['website'].get_current_website()

        def is_visible(cat):
            restricts = cat.public_website_ids | cat.website_id
            return not restricts or website in restricts

        if 'categories' in values:
            vals['categories'] = values['categories'].filtered(is_visible)
        if 'category_entries' in values:
            vals['category_entries'] = values['category_entries'].filtered(is_visible)
        if 'search_categories_ids' in values:
            all_cats = request.env['product.public.category'].browse(values['search_categories_ids'])
            vals['search_categories_ids'] = all_cats.filtered(is_visible).ids

        return vals
