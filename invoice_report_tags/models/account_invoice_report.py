# -*- coding: utf-8 -*-
from odoo import api, fields, models

# ---------------------------------------------------------------------------
# ``crm.tag`` is a single flat field doing four different jobs on sale orders.
# Only the first group describes *what was sold*, which is the "Sale Type"
# dimension David asked for. An allowlist (rather than a blacklist of the
# others) is deliberate: shipment container codes are added every shipment, so
# a blacklist would silently leak new codes into the report as fake sale types.
#
#   1. Sale type  — what was sold. Allowlisted below.
#   2. Fulfilment status — Paid, Payment email, HOLD, booked, ready, yard,
#      done, collected, pic reminder.
#   3. Pickup location — Cage (the pickup cage customers collect from).
#   4. Shipment container codes — AUSC6/7/8, NZC24/25, USAC7/10/12,
#      ukc19/20/21. One per container, so this list grows continuously.
#
# To add a new sale type: add its name here (lowercase) and bump the module
# version so the migration recomputes existing invoices.
# ---------------------------------------------------------------------------
SALE_TYPE_TAGS = frozenset({
    'retaining wall',
    'fence',
    'kitset planter',
    'one piece planter',
    'ff edging',
    'ft edging',
    'steps',
    'rainscreen',
    'tree rings',
    'colour sample',
    'steel merchant product',
})


def is_sale_type_tag(tag):
    """Return whether ``tag`` names a sale type rather than status/pickup/container.

    Matched on a normalised name because ``crm.tag.name`` is translated and the
    en_NZ/en_US values differ in case (e.g. "Steps" vs "steps").
    """
    name = tag.name or ''
    return ' '.join(name.split()).lower() in SALE_TYPE_TAGS


class AccountMove(models.Model):
    """Store the source sale order's sale-type tags on the invoice.

    ``sale_type_ids`` is a stored computed field so report models can group a
    pivot by it: Odoo only groups by a stored field, or by a related field
    whose path is many2one-only. The invoice -> sale order link goes through
    ``line_ids`` (one2many) and ``sale_line_ids`` (many2many), which can't be
    traversed for grouping, so we materialise the tags here on ``account.move``.
    """
    _inherit = 'account.move'

    sale_type_ids = fields.Many2many(
        'crm.tag', string='Sale Type',
        compute='_compute_sale_type_ids', store=True,
        help="What was sold, taken from the source sales order's tags. "
             "Excludes fulfilment status, pickup location and container codes.")

    @api.depends('line_ids.sale_line_ids.order_id.tag_ids')
    def _compute_sale_type_ids(self):
        empty = self.env['crm.tag']
        for move in self:
            tags = empty
            for line in move.line_ids:
                for sale_line in line.sale_line_ids:
                    tags |= sale_line.order_id.tag_ids
            move.sale_type_ids = tags.filtered(is_sale_type_tag)


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
