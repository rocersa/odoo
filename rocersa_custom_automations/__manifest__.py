{
    "name": "Rocersa Custom Automations",
    "summary": "Checks and balances to ensure Rocersa workflows are assigned and followed.",
    "version": "19.0.1.3.0",
    "category": "Inventory",
    "depends": [
        "sale",
        "stock_delivery",
        "mail",
    ],
    "data": [
        "views/stock_picking_type_views.xml",
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
