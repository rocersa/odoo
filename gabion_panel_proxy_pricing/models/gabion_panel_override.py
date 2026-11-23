from odoo import fields, models


class GabionPanelOverride(models.Model):
    _name = "gabion.panel.override"
    _description = "Gabion Panel Length Proxy"
    _order = "current_length"

    current_length = fields.Integer(
        string="Panel Length",
        required=True,
        index=True,
        help="A panel dimension (mm) the catalogue does not sell as a standard length.",
    )
    proxy_length = fields.Integer(
        string="Priced As",
        required=True,
        help="The standard length the storefront prices this dimension at.",
    )

    _current_length_uniq = models.Constraint(
        "UNIQUE(current_length)",
        "Each panel length can only have one proxy length.",
    )
