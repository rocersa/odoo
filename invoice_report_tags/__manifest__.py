# -*- coding: utf-8 -*-
{
    'name': "Invoice Report Tags",

    'summary': """
        Add Customer Type (partner tag) and Sale Type (sale tag) as
        groupable dimensions on the Invoice Analysis report.
    """,

    'description': """
        Extends ``account.invoice.report`` with two groupable fields so
        "average invoice value by customer type / sale type" can be read
        directly from Accounting > Reporting > Invoice Analysis:

        - **Customer Type** — the invoice customer's partner tags
          (``res.partner.category``), via a related field.
        - **Sale Type** — what was sold, taken from the source sales order's
          ``crm.tag`` values via ``account.move.line.sale_line_ids``. That
          field also carries fulfilment status, pickup location (the pickup
          cage) and per-shipment container codes, so sale types are matched
          against an explicit allowlist in ``models/account_invoice_report.py``.

        Reported at invoice level via ``rocersa.invoice.report`` (one row per
        invoice), so the pivot's Average is the true average invoice value.
        The standard ``account.invoice.report`` is line-level, where an
        average would be average unit price instead.

        Requested by David Bird (2026-08-23) to self-serve average invoice
        value broken down by what was sold and who bought it.
    """,

    'author': "Harry",
    'category': 'Accounting/Reporting',
    'version': '0.9',

    'depends': ['account', 'sale', 'crm'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice_report_views.xml',
        'views/rocersa_invoice_report_views.xml',
    ],
}
