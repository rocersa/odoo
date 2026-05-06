from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    activity_trigger = fields.Selection([
        ('none', 'None'),
        ('courier', 'Book Courier'),
        ('collect_ready', 'Inform Customer - Ready for Collection'),
    ], string='Activity Trigger', default='none',
    help="When a picking of this type becomes Ready, automatically create the selected activity.")
