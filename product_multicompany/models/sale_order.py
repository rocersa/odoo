# -*- coding: utf-8 -*-

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.constrains('company_id', 'order_line')
    def _check_order_line_company_id(self):
        for order in self:
            bad_lines = order.order_line.filtered(
                lambda l: l.product_id._get_effective_company_ids()
                and order.company_id not in l.product_id._get_effective_company_ids()
            )
            if bad_lines:
                bad_products = bad_lines.product_id.mapped('display_name')
                raise models.ValidationError(
                    "The following products are not available in the company '%s': %s"
                    % (order.company_id.display_name, ', '.join(bad_products))
                )
