# -*- coding: utf-8 -*-
{
    'name': "Brand Report Layout",

    'summary': """
        Document layout for Cor-Ten-Steel, Gabion1 and Rocersa: the striped
        layout with repositioned addresses and document number.
    """,

    'description': """
        Custom document layout (see ``docs/brand/design-standard.md`` §9).

        Based on the standard **striped** layout, with three changes:

        - company address **right-aligned** in the header (as in *bold*),
        - customer address **left-aligned**,
        - document (invoice) number **right-aligned, on the same line as the
          customer address** (as in *bubble*).

        Implemented as an inheritance of ``web.external_layout_striped`` so the
        layout keeps the striped styling and the per-company colour overrides in
        ``res.company.scss``. Set a company's *Document Layout* to **Striped** to
        use it.
    """,

    'author': "Harry",
    'category': 'Rocersa/Brand',
    'version': '0.5',

    'depends': ['web'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
    'data': [
        'views/report_templates.xml',
        'views/report_assets.xml',
    ],
    'post_init_hook': 'post_init_hook',
}
