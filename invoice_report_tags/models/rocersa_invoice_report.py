# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.sql import SQL

from .account_invoice_report import sale_type_tags_for_moves


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
        related='partner_id.category_id')
    sale_type_ids = fields.Many2many(
        'crm.tag', string='Sale Type',
        compute='_compute_sale_type_ids', search='_search_sale_type_ids')
    amount_total = fields.Monetary(
        string='Total', readonly=True, currency_field='currency_id')
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

    @api.depends('move_id')
    def _compute_sale_type_ids(self):
        move_tags = sale_type_tags_for_moves(self.env, self.mapped('move_id'))
        empty = self.env['crm.tag']
        for rec in self:
            rec.sale_type_ids = move_tags.get(rec.move_id.id, empty)

    def _search_sale_type_ids(self, operator, value):
        if operator in ('=', '!='):
            operator = 'in' if operator == '=' else 'not in'
        if operator not in ('in', 'not in'):
            return [('id', 'in', [])]
        orders = self.env['sale.order'].search([('tag_ids', operator, value)])
        return [('move_id', operator, orders.invoice_ids.ids)]
