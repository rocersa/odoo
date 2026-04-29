{
    'name': 'Mail From Company',
    'version': '1.0.0',
    'summary': 'Prepend company name to the From header in outgoing emails',
    'description': """
        In a multi-company setup, this module prepends the record's company name
        to the user's display name in the From header of outgoing emails.

        Example: "Company B | Harry" <harry@example.com>
    """,
    'category': 'Productivity/Discuss',
    'depends': ['mail'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
