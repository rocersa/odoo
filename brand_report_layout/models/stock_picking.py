# -*- coding: utf-8 -*-
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _brand_amalgamated_lines(self):
        """One line per product for the internal-transfer picklist.

        Odoo keeps a separate ``stock.move`` per element and never merges a
        component shared by several kits (``description_picking``, which carries
        the kit name, is a merge-distinct field). For the printed internal
        transfer we want the total to pick per component, so group the moves by
        product and sum the quantity and the weight.

        :returns: a list of ``{'product', 'quantity', 'weight'}`` dicts, sorted
            by product code then name.
        """
        self.ensure_one()
        groups = self.move_ids.filtered(
            lambda m: m.quantity and m.product_id
        ).grouped(lambda m: (m.product_id, m.product_uom))
        lines = [{
            'product': moves[0].product_id,
            'quantity': sum(moves.mapped('quantity')),
            'weight': sum(moves.mapped(lambda m: m.quantity * m.product_id.weight)),
        } for moves in groups.values()]
        return sorted(
            lines,
            key=lambda line: (line['product'].default_code or '', line['product'].name or ''),
        )
