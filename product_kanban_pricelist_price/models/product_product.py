from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    pricelist_price = fields.Float(
        string="Pricelist Price",
        compute='_compute_pricelist_price',
        help="Unit price for a quantity of 1 according to the company's pricelist.",
    )
    pricelist_currency_id = fields.Many2one(
        'res.currency',
        string="Pricelist Currency",
        compute='_compute_pricelist_price',
    )

    def _compute_pricelist_price(self):
        pricelist = self.env['product.pricelist']._get_company_pricelist()
        self.pricelist_currency_id = pricelist.currency_id or self.env.company.currency_id
        if pricelist:
            prices = pricelist._get_products_price(
                self, 1.0, date=fields.Date.context_today(self),
            )
            for product in self:
                product.pricelist_price = prices.get(product.id, product.lst_price)
        else:
            for product in self:
                product.pricelist_price = product.lst_price
