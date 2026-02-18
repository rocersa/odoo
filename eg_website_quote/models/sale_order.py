from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_rfq_from_website = fields.Boolean(string="Request from Website")