# -*- coding: utf-8 -*-
"""Retire this module on the Odoo 20 upgrade.

Odoo 20's shop controller now computes attribute filter values from the base
product set (website_sale/controllers/main.py:472-473, :633-637), so this
module is redundant. Its view anchors do not resolve on 20; remove it before
the module is loaded.
"""
from odoo.upgrade import util


def migrate(cr, version):
    util.remove_module(
        cr, 'website_sale_product_attribute_value_filter_existing')
