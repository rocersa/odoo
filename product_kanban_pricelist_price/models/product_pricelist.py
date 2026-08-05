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
