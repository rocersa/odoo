# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.tools.sql import SQL


class RocersaInvoiceReport(models.Model):
    """Invoice-level report (one row per customer invoice).

    Unlike ``account.invoice.report`` (line-level), this report has one row
    per ``account.move``, so a pivot's "Average" of ``amount_total`` is the
    true *average invoice value* — the metric David asked for — rather than a
    per-line average.
    """
    _name = 'rocersa.invoice.report'
    _description = 'Invoice Value Report (invoice-level)'
    _auto = False
    _rec_name = 'name'
    _order = 'invoice_date desc, id desc'

    name = fields.Char(string='Number', readonly=True)
    move_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    customer_type_ids = fields.Many2many(
        'res.partner.category', string='Customer Type',
        related='partner_id.category_id', compute_sudo=True)
    sale_type_ids = fields.Many2many(
        'crm.tag', string='Sale Type',
        related='move_id.sale_type_ids', compute_sudo=True)
    amount_total = fields.Monetary(
        string='Total', readonly=True, currency_field='currency_id',
        aggregator='avg')
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount', readonly=True, currency_field='currency_id')
    invoice_date = fields.Date(string='Invoice Date', readonly=True)
    move_type = fields.Char(string='Type', readonly=True)
    state = fields.Char(string='Status', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)

    @property
    def _table_query(self):
        return SQL("""
            SELECT
                move.id AS id,
                move.id AS move_id,
                move.name AS name,
                move.partner_id AS partner_id,
                move.amount_total AS amount_total,
                move.amount_untaxed AS amount_untaxed,
                move.invoice_date AS invoice_date,
                move.move_type AS move_type,
                move.state AS state,
                move.company_id AS company_id,
                move.currency_id AS currency_id
            FROM account_move move
            WHERE move.move_type IN ('out_invoice', 'out_refund')
        """)
