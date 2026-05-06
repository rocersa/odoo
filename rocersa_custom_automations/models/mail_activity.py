from odoo import _, models
from odoo.exceptions import UserError


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def action_feedback(self, feedback=False, attachment_ids=None):
        for activity in self:
            if activity.res_model != 'stock.picking':
                continue
            picking = self.env['stock.picking'].sudo().browse(activity.res_id).exists()
            if not picking:
                continue
            if picking.picking_type_id.activity_trigger == 'courier' and activity.summary == 'Book Courier':
                if not picking.carrier_id:
                    raise UserError(_('Please select a carrier before marking this activity as done.'))
                if not picking.carrier_tracking_ref:
                    raise UserError(_('Please enter a tracking reference before marking this activity as done.'))
        return super().action_feedback(feedback=feedback, attachment_ids=attachment_ids)
