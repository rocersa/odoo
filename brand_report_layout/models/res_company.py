# -*- coding: utf-8 -*-
from odoo import models

# Brand palettes — docs/brand/design-standard.md §3.
# (company-name prefix, primary, secondary). Email button colour = primary;
# its text stays the Odoo default white.
BRAND_COLORS = [
    ('Corten Steel', '#FC7F24', '#f1f2f4'),
    ('Gabion1', '#2B7C26', '#f1f2f4'),
    ('Rocersa', '#4b8763', '#005522'),
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    def apply_brand_colors(self):
        """Set each company's report/email colours from the brand palette.

        Called from ``data/company_colors.xml`` on install and every upgrade,
        so the standard is enforced rather than hand-set. Companies are matched
        by name prefix, so a new country company inherits its brand's colours
        automatically. Reversible: the previous values are ordinary company
        settings.
        """
        for prefix, primary, secondary in BRAND_COLORS:
            companies = self.search([('name', '=like', prefix + '%')])
            if companies:
                companies.write({
                    'primary_color': primary,
                    'secondary_color': secondary,
                    'email_secondary_color': primary,
                })
        return True
