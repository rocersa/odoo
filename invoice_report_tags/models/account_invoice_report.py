# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    customer_type_ids = fields.Many2many(
        'res.partner.category',
        string='Customer Type',
        related='partner_id.category_id',
    )

    sale_type_ids = fields.Many2many(
        'crm.tag',
        string='Sale Type',
        compute='_compute_sale_type_ids',
        search='_search_sale_type_ids',
    )

    # Workflow/status tags that share the ``crm.tag`` field with the real
    # product-type ("sale type") tags. Filtered out so "Sale Type" only
    # shows what was sold (Retaining wall, Fence, Cage, planters, steps,
    # edging, ...), not fulfilment status (Paid, booked, ready, yard, done,
    # collected, ...). Kept as a module constant so it's tracked in-repo and
    # easy to update when the tag set changes.
    SALE_STATUS_TAGS = frozenset({
        'Paid', 'Payment email', 'HOLD', 'booked', 'collected', 'done',
        'pic reminder', 'ready', 'yard',
    })

    @api.depends('move_id')
    def _compute_sale_type_ids(self):
        moves = self.mapped('move_id')
        # Resolve sale orders from invoices through the sale order's
        # "Invoices" smart button (sale.order.invoice_ids) — the strong link
        # back from invoice to sale order.
        orders = self.env['sale.order'].search([('invoice_ids', 'in', moves.ids)])
        empty = self.env['crm.tag']
        move_tags = {}
        for order in orders:
            tags = order.tag_ids.filtered(
                lambda t: t.name not in self.SALE_STATUS_TAGS)
            for move in order.invoice_ids:
                move_tags[move.id] = move_tags.get(move.id, empty) | tags
        for rec in self:
            rec.sale_type_ids = move_tags.get(rec.move_id.id, empty)

    def _search_sale_type_ids(self, operator, value):
        # Grouping support for the non-stored computed field: translate a
        # tag filter into an invoice filter via the sale order link.
        if operator in ('=', '!='):
            operator = 'in' if operator == '=' else 'not in'
        if operator not in ('in', 'not in'):
            return [('id', 'in', [])]
        orders = self.env['sale.order'].search([('tag_ids', operator, value)])
        return [('move_id', operator, orders.invoice_ids.ids)]
