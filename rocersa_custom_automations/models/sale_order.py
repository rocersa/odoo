from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, vals):
        res = super().write(vals)
        if 'delivery_status' in vals:
            for order in self:
                if order.delivery_status == 'full':
                    order._create_customer_followup_activity()
        return res

    def _create_customer_followup_activity(self):
        """Create a follow-up activity if one does not already exist."""
        self.ensure_one()
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            return
        existing = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
            ('summary', '=', 'Follow Up – Project Feedback'),
        ], limit=1)
        if existing:
            return
        user_id = self.user_id.id or self.env.uid
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=user_id,
            summary='Follow Up – Project Feedback',
            date_deadline=fields.Date.context_today(self) + relativedelta(months=3),
            note=_(
                'Order %(order)s has been fully shipped. Please follow up with the customer to ask how the project went.',
                order=self.name,
            ),
        )

    def _check_shipping_method(self):
        """Return an error message if the order lacks a shipping method."""
        self.ensure_one()
        if not self.carrier_id and not self.is_all_service:
            return _("Please select a shipping method before sending this order.")
        return False

    def _confirmation_error_message(self):
        error = super()._confirmation_error_message()
        if error:
            return error
        return self._check_shipping_method()

    def action_quotation_send(self):
        for order in self:
            error = order._check_shipping_method()
            if error:
                raise UserError(error)
        return super().action_quotation_send()
