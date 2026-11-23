{
    "name": "Gabion Panel Proxy Pricing",
    "summary": "Price non-standard Gabion panel lengths at the storefront's proxy length.",
    "version": "19.0.1.0.0",
    "category": "Sales/Sales",
    "author": "Rocersa",
    "license": "AGPL-3",
    "depends": [
        "product",
        "sale",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/gabion_panel_override_data.xml",
        "views/gabion_panel_override_views.xml",
    ],
    "installable": True,
    "application": False,
}
