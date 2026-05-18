from odoo import models


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    @api.model_create_multi
    def create(self, vals_list):
        partials = super().create(vals_list)
        for move in (partials.debit_move_id + partials.credit_move_id).move_id:
            if not move.is_invoice():
                continue
            if not move.currency_id.is_zero(move.amount_residual):
                continue
            # Invoice is fully paid – check for Ready pickings that need the activity
            sale_orders = move.invoice_line_ids.sale_line_ids.order_id
            for so in sale_orders:
                for picking in so.picking_ids.filtered(
                    lambda p: p.state == 'assigned' and p.picking_type_id.activity_trigger == 'picklist_yard'
                ):
                    picking._create_picklist_yard_activity()
        return partials
