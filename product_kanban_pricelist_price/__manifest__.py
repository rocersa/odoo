{
    'name': 'Product Kanban Pricelist Price',
    'summary': "Show the company pricelist price on product kanban cards",
    'description': """
Replaces the static catalog price (list_price/lst_price) on product kanban
cards with the unit price computed from the company's pricelist (including
customer taxes, i.e. GST), so users can check real sales prices without
creating dummy quotes.
""",
    'version': '19.0.1.2.0',
    'category': 'Sales',
    'author': 'Rocersa',
    'license': 'LGPL-3',
    'depends': ['product'],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
}
