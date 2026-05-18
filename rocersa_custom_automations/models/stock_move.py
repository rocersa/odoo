from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self, force_qty=False):
        pickings_before = self.mapped('picking_id')
        states_before = {p.id: p.state for p in pickings_before}
        res = super()._action_assign(force_qty=force_qty)
        for picking in self.mapped('picking_id').filtered(
            lambda p: p.picking_type_id.activity_trigger != 'none'
            and p.state == 'assigned'
            and states_before.get(p.id) != 'assigned'
        ):
            if picking.picking_type_id.activity_trigger == 'courier':
                picking._create_courier_booking_activity()
            elif picking.picking_type_id.activity_trigger == 'collect_ready':
                picking._create_collect_ready_activity()
            elif picking.picking_type_id.activity_trigger == 'picklist_yard':
                picking._create_picklist_yard_activity()
        return res
