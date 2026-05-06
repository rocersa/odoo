from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_activity_assignee(self):
        """Return the user ID who should be assigned to the activity.

        Priority:
        1. Picking Responsible (user_id)
        2. Sales Order Salesperson (sale_id.user_id) if sale_stock is installed
        3. Current user
        """
        self.ensure_one()
        user_id = self.user_id.id
        if not user_id and hasattr(self, 'sale_id') and self.sale_id:
            user_id = self.sale_id.user_id.id
        if not user_id:
            user_id = self.env.uid
        return user_id

    def _create_courier_booking_activity(self):
        """Create a 'Book Courier' activity if one does not already exist."""
        self.ensure_one()
        if self.picking_type_id.activity_trigger != 'courier':
            return
        if self.carrier_id and self.carrier_tracking_ref:
            return
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            return
        existing = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
            ('summary', '=', 'Book Courier'),
        ], limit=1)
        if existing:
            return
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=self._get_activity_assignee(),
            summary='Book Courier',
            note=_(
                'The delivery %(picking)s is ready. Please book the courier and fill in the tracking reference.',
                picking=self.name,
            ),
        )

    def _create_collect_ready_activity(self):
        """Create an 'Inform Customer - Ready for Collection' activity if one does not already exist."""
        self.ensure_one()
        if self.picking_type_id.activity_trigger != 'collect_ready':
            return
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            return
        existing = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
            ('summary', '=', 'Inform Customer - Ready for Collection'),
        ], limit=1)
        if existing:
            return
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=self._get_activity_assignee(),
            summary='Inform Customer - Ready for Collection',
            note=_(
                'The order %(picking)s is ready for collection. Please inform the customer.',
                picking=self.name,
            ),
        )

    def _validation_error_message(self):
        """Return an error message if the picking should not be validated."""
        self.ensure_one()
        if self.picking_type_id.activity_trigger == 'courier':
            if not self.carrier_id:
                return _('Please select a carrier before validating this delivery.')
            if not self.carrier_tracking_ref:
                return _('Please enter a tracking reference before validating this delivery.')
        return False

    def button_validate(self):
        for picking in self:
            error = picking._validation_error_message()
            if error:
                raise UserError(error)
        return super().button_validate()
