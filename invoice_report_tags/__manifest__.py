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
        - **Sale Type** — the sale order's product-type tags (``crm.tag``),
          resolved through the sale order's Invoices smart button
          (``sale.order.invoice_ids``) and filtered to exclude the
          workflow/status tags that share the same field.

        Requested by David Bird (2026-08-23) to self-serve average invoice
        value broken down by what was sold and who bought it.
    """,

    'author': "Harry",
    'category': 'Accounting/Reporting',
    'version': '0.4',

    'depends': ['account', 'sale', 'crm'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
    'data': [
        'views/account_invoice_report_views.xml',
        'views/rocersa_invoice_report_views.xml',
    ],
}
