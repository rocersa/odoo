# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Workflow/status tags that share the ``crm.tag`` field with the real
# product-type ("sale type") tags. Filtered out so "Sale Type" only shows
# what was sold (Retaining wall, Fence, Cage, planters, steps, edging, ...),
# not fulfilment status (Paid, booked, ready, yard, done, collected, ...).
SALE_STATUS_TAGS = frozenset({
    'Paid', 'Payment email', 'HOLD', 'booked', 'collected', 'done',
    'pic reminder', 'ready', 'yard',
})


class AccountMove(models.Model):
    """Store the source sale order's product-type tags on the invoice.

    ``sale_type_ids`` is a stored computed field so report models can group a
    pivot by it: Odoo only groups by a stored field, or by a related field
    whose path is many2one-only. The invoice -> sale order link goes through
    ``line_ids`` (one2many) and ``sale_line_ids`` (many2many), which can't be
    traversed for grouping, so we materialise the tags here on ``account.move``.
    """
    _inherit = 'account.move'

    sale_type_ids = fields.Many2many(
        'crm.tag', string='Sale Type',
        compute='_compute_sale_type_ids', store=True)

    @api.depends('line_ids.sale_line_ids.order_id.tag_ids')
    def _compute_sale_type_ids(self):
        empty = self.env['crm.tag']
        for move in self:
            tags = empty
            for line in move.line_ids:
                for sale_line in line.sale_line_ids:
                    tags |= sale_line.order_id.tag_ids
            move.sale_type_ids = tags.filtered(
                lambda t: t.name not in SALE_STATUS_TAGS)


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    customer_type_ids = fields.Many2many(
        'res.partner.category',
        string='Customer Type',
        related='partner_id.category_id',
        compute_sudo=True,
    )

    sale_type_ids = fields.Many2many(
        'crm.tag',
        string='Sale Type',
        related='move_id.sale_type_ids',
        compute_sudo=True,
    )
