from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
