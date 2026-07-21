{
    "name": "Website PostHog Experiments",
    "summary": "A/B test website pages with PostHog experiments",
    "version": "19.0.1.0.5",
    "category": "Website",
    "author": "Rocersa",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "website",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/website_experiment_views.xml",
        "views/res_config_settings_views.xml",
        "views/website_templates.xml",
    ],
}
