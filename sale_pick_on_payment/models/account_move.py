# -*- coding: utf-8 -*-

from odoo import models

from .sale_order import SETTLED_PAYMENT_STATES


class AccountMove(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        res = super()._invoice_paid_hook()
        for invoice in self:
            if invoice.state != "posted" or invoice.move_type != "out_invoice":
                continue
            if invoice.payment_state not in SETTLED_PAYMENT_STATES:
                continue
            orders = invoice.invoice_line_ids.sale_line_ids.order_id
            orders._sale_pick_create_if_paid()
        return res
