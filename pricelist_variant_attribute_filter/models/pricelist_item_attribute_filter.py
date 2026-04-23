from odoo import api, fields, models


class PricelistItemAttributeFilter(models.Model):
    _name = 'pricelist.item.attribute.filter'
    _description = "Pricelist Item Attribute Filter"

    pricelist_item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        string="Pricelist Item",
        required=True,
        ondelete='cascade',
        index=True,
    )
    attribute_id = fields.Many2one(
        comodel_name='product.attribute',
        string="Attribute",
        required=True,
        ondelete='cascade',
    )
    value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        relation='pricelist_attr_filter_value_rel',
        column1='filter_id',
        column2='value_id',
        string="Values",
        required=True,
    )
    product_tmpl_id = fields.Many2one(
        related='pricelist_item_id.product_tmpl_id',
        store=True,
    )
    available_value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        compute='_compute_available_value_ids',
    )

    @api.depends('attribute_id', 'product_tmpl_id')
    def _compute_available_value_ids(self):
        for rec in self:
            if rec.attribute_id and rec.product_tmpl_id:
                line = rec.product_tmpl_id.attribute_line_ids.filtered(
                    lambda l: l.attribute_id == rec.attribute_id
                )
                rec.available_value_ids = line.value_ids
            else:
                rec.available_value_ids = False

    @api.onchange('attribute_id')
    def _onchange_attribute_id(self):
        self.value_ids = False
