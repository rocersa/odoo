from odoo import models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _get_company_pricelist(self, company=None):
        """Return the pricelist used to display product prices for a company.

        Each company uses a single pricelist; fall back to the first
        shared/company pricelist by sequence, mirroring core's own fallback.
        """
        company = company or self.env.company
        return self.search(
            [('company_id', 'in', [company.id, False])],
            order='sequence, id',
            limit=1,
        )

    def _get_products_price_tax_included(self, products, date=False):
        """Return {product_id: unit price incl. customer taxes} for quantity 1.

        Falls back to the product's catalog price when self is empty or no
        rule applies. Works on product.template and product.product records.
        """
        currency = self.currency_id or self.env.company.currency_id
        prices = self._get_products_price(products, 1.0, date=date) if self else {}
        result = {}
        for product in products:
            if product.id in prices:
                price = prices[product.id]
            elif product._name == 'product.product':
                price = product.lst_price
            else:
                price = product.list_price
            taxes = product.taxes_id
            if taxes:
                price = taxes.compute_all(
                    price, currency=currency, quantity=1.0, product=product,
                )['total_included']
            result[product.id] = price
        return result
