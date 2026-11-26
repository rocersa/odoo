# -*- coding: utf-8 -*-
{
    "name": "Barcode Yard Relocate",
    "version": "19.0.1.0.1",
    "summary": "Move a product's full quantity between locations from the barcode app",
    "description": """
Yard relocate
=============

Adds **Move stock** to the barcode app's home screen, so the yard can move
stock between locations from the floor without asking the back office.

The operator scans the source location, scans the destination location, then
scans each product that is physically there. Each scan queues that product's
**entire on-hand quantity at the scanned location** (nothing moves yet); one
**Confirm** commits the whole list.

- Scope is the exact scanned source location only: stock split into a child
  location stays put.
- Source and destination must differ; a product with no stock at the source
  gets a warning and is skipped; an empty list does nothing.
- Moves go through ``stock.quant.move_quants`` with a reference of
  ``Yard relocate: <source> -> <destination> (user)`` and packages stay intact.
- Access is ``stock.group_stock_user``: yard staff need no Inventory Manager.

This module is a thin client action that reuses the barcode scanner component;
it does not modify upstream ``stock_barcode``.
""",
    "author": "Rocersa",
    "category": "Rocersa/Warehouse",
    "license": "AGPL-3",
    "depends": ["stock_barcode"],
    "data": [
        "security/ir.model.access.csv",
        "views/yard_relocate_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "stock_barcode_yard_relocate/static/src/yard_relocate/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
