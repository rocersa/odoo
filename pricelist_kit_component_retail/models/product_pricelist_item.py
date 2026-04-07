from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    base = fields.Selection(
        selection_add=[
            ('bom_component_pricelist', 'Component Retail Prices (BoM)'),
        ],
        ondelete={'bom_component_pricelist': 'set default'},
    )
    component_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Component Pricelist",
        check_company=True,
        help="Pricelist applied to each BoM component to obtain its retail price. "
             "The kit price will be the sum of all component retail prices.",
    )

    def _compute_base_price(self, product, quantity, uom, date, currency, **kwargs):
        rule_base = self.base or 'list_price'
        if rule_base != 'bom_component_pricelist' or not self.component_pricelist_id:
            return super()._compute_base_price(product, quantity, uom, date, currency, **kwargs)

        product.ensure_one()

        # Resolve the actual product.product record
        if product._name == 'product.template':
            product_product = product.product_variant_id
        else:
            product_product = product

        bom = self.env['mrp.bom']._bom_find(product_product).get(product_product)
        if not bom:
            return super()._compute_base_price(product, quantity, uom, date, currency, **kwargs)

        component_pricelist = self.component_pricelist_id
        total = 0.0
        for line in bom.bom_line_ids:
            if line._skip_bom_line(product_product):
                continue
            component_price = component_pricelist._get_product_price(
                line.product_id,
                line.product_qty,
                currency=component_pricelist.currency_id,
                uom=line.product_uom_id,
                date=date,
            )
            total += component_price * line.product_qty

        # Normalize to per-unit price for the BoM product
        if bom.product_qty:
            total = total / bom.product_qty

        # Convert from component pricelist currency to the requested currency
        src_currency = component_pricelist.currency_id or self.env.company.currency_id
        if src_currency != currency:
            total = src_currency._convert(total, currency, self.env.company, date, round=False)

        # Convert from BoM product UoM to requested UoM
        product_uom = product.uom_id
        if product_uom != uom:
            total = product_uom._compute_price(total, uom)

        return total
