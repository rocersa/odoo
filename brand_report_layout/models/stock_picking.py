# -*- coding: utf-8 -*-
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _brand_amalgamated_lines(self):
        """One line per product and source location for the picklist.

        Odoo keeps a separate ``stock.move`` per element and never merges a
        component shared by several kits (``description_picking``, which carries
        the kit name, is a merge-distinct field). For the printed transfer we
        want the total to pick per component, so group the moves by product and
        sum the quantity and the weight.

        Each line also carries its source location so the picker can see where
        the part actually sits (the reserved move-line location, which may be a
        rack or bay below the picking's source). A product stored in more than
        one location prints one line per location.

        :returns: a list of ``{'product', 'location', 'quantity', 'weight'}``
            dicts, sorted by product code, name then source location.
        """
        self.ensure_one()

        def source_location(move):
            locations = move.move_line_ids.mapped('location_id')
            return locations[:1] if len(locations) == 1 else move.location_id

        groups = self.move_ids.filtered(
            lambda m: m.quantity and m.product_id
        ).grouped(lambda m: (m.product_id, m.product_uom, source_location(m)))
        lines = [{
            'product': moves[0].product_id,
            'location': source_location(moves[0]),
            'quantity': sum(moves.mapped('quantity')),
            'weight': sum(moves.mapped(lambda m: m.quantity * m.product_id.weight)),
        } for moves in groups.values()]
        return sorted(
            lines,
            key=lambda line: (
                line['product'].default_code or '',
                line['product'].name or '',
                line['location'].complete_name or '',
            ),
        )
