# -*- coding: utf-8 -*-
{
    "name": "Corten Magnet Label",
    "version": "19.0.1.0.15",
    "summary": "Print the magnetic C-channel label for a product or storage location",
    "description": """
Magnetic label report
=====================

Adds **Print → Magnet Label** to products and storage locations. The report is
the 72 x 70 mm mono artwork for the AMF 80 mm C-channel magnetic strip, printed
on the Epson TM-m30III: barcode, human-readable code and the Odoo record name.

The artwork is rendered server-side as a PNG and embedded in a true-size PDF,
so the Odoo preview is what the printer receives. Code 128B is encoded in the
module; the only dependency is Pillow, which Odoo already ships.

The barcode carries the record's Odoo barcode, falling back to the internal
reference when no barcode is set. Scanning resolves in Odoo only when the
encoded value matches the database, so populate `barcode` on locations and
products before a stocktake relies on it.
""",
    "author": "Rocersa",
    "category": "Rocersa/Warehouse",
    "license": "AGPL-3",
    "depends": ["base", "product", "stock"],
    "data": [
        "report/paperformat.xml",
        "report/report_label.xml",
        "report/report_actions.xml",
    ],
    "installable": True,
    "application": False,
}
