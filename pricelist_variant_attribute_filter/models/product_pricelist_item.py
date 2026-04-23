from odoo import _, api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    has_attribute_filter = fields.Boolean(
        compute='_compute_has_attribute_filter',
        store=True,
    )

    custom_name = fields.Char(
        string="Rule Name",
        help="Optional label for this pricelist rule. "
             "Overrides the auto-generated 'Applied On' name.",
    )

    attribute_filter_ids = fields.One2many(
        comodel_name='pricelist.item.attribute.filter',
        inverse_name='pricelist_item_id',
        string="Variant Attribute Filters",
        help="When set, this rule only applies to variants whose attribute "
             "values match ALL filter lines (AND across attributes, OR within "
             "each attribute's selected values). Leave empty to apply to all "
             "variants of the product.",
    )

    @api.depends('attribute_filter_ids')
    def _compute_has_attribute_filter(self):
        for item in self:
            item.has_attribute_filter = bool(item.attribute_filter_ids)

    @api.depends('applied_on', 'categ_id', 'product_tmpl_id', 'product_id',
                 'attribute_filter_ids', 'custom_name')
    def _compute_name(self):
        for item in self:
            if item.custom_name:
                item.name = item.custom_name
            else:
                super(ProductPricelistItem, item)._compute_name()

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        super()._onchange_product_tmpl_id()
        # Clear attribute filters when template changes
        for item in self:
            if not item.product_tmpl_id:
                item.attribute_filter_ids = False
            elif item.attribute_filter_ids:
                # Remove filter lines for attributes not on the new template
                tmpl_attr_ids = item.product_tmpl_id.attribute_line_ids.attribute_id.ids
                to_remove = item.attribute_filter_ids.filtered(
                    lambda f: f.attribute_id.id not in tmpl_attr_ids
                )
                if to_remove:
                    item.attribute_filter_ids -= to_remove

    def _is_applicable_for(self, product, qty_in_product_uom):
        """Extend to check attribute filters on template-level rules."""
        res = super()._is_applicable_for(product, qty_in_product_uom)
        if not res or not self.attribute_filter_ids:
            return res

        # Attribute filters only make sense for product.product records
        if product._name == 'product.template':
            # If template has a single variant, resolve it
            if product.product_variant_count == 1:
                product = product.product_variant_id
            else:
                # Cannot match attribute filters against a multi-variant template
                return False

        # Get the product.attribute.value ids on this variant
        variant_attr_value_ids = product.product_template_attribute_value_ids.product_attribute_value_id

        # AND across filter lines: every filter line must be satisfied
        # OR within a filter line: variant must have at least one of the values
        for attr_filter in self.attribute_filter_ids:
            variant_values_for_attr = variant_attr_value_ids.filtered(
                lambda v: v.attribute_id == attr_filter.attribute_id
            )
            if not (variant_values_for_attr & attr_filter.value_ids):
                return False

        return True
