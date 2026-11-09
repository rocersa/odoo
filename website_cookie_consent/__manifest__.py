{
    "name": "Website Cookie Consent (UK)",
    "summary": "Apex-domain prior consent banner for UK websites (PECR)",
    "version": "19.0.1.0.0",
    "category": "Website",
    "author": "Rocersa",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "website",
    ],
    "data": [
        "views/website_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_cookie_consent/static/src/js/consent.js",
        ],
    },
}
