from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pricelist_price = fields.Float(
        string="Pricelist Price",
        compute='_compute_pricelist_price',
        help="Unit price for a quantity of 1 according to the company's "
             "pricelist, including customer taxes (GST).",
    )
    pricelist_currency_id = fields.Many2one(
        'res.currency',
        string="Pricelist Currency",
        compute='_compute_pricelist_price',
    )

    def _compute_pricelist_price(self):
        pricelist = self.env['product.pricelist']._get_company_pricelist()
        self.pricelist_currency_id = pricelist.currency_id or self.env.company.currency_id
        prices = pricelist._get_products_price_tax_included(
            self, date=fields.Date.context_today(self),
        )
        for template in self:
            template.pricelist_price = prices[template.id]
