# -*- coding: utf-8 -*-
{
    'name': "Stock Reorder Advisor",

    'summary': """
        Adds demand-pattern analysis and guided reorder-point suggestions for
        slow-moving, intermittent and lumpy-demand products.
    """,

    'description': """
        Helps stock planners optimise min/max levels by computing:
        - demand pattern classification (smooth, erratic, intermittent, lumpy)
        - historical order size and interval statistics
        - lead-time demand and safety-stock suggestions
        - stockout-risk indicators and contextual advisor messages

        Designed for large, slow-selling ranges where average-demand
        forecasting is misleading and order lumpiness drives stockouts.
    """,

    'author': "Harry",
    'category': 'Inventory',
    'version': '0.7',

    'depends': ['stock', 'purchase_stock'],
    'application': False,
    'installable': True,

    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/res_company_views.xml',
        'views/stock_warehouse_orderpoint_views.xml',
        'views/reorder_suggestion_report_views.xml',
    ],

    'license': 'AGPL-3',
}
