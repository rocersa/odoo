# -*- coding: utf-8 -*-


def post_init_hook(env):
    """Apply the brand palettes when the module is installed.

    Uses ``res.company.apply_brand_colors`` (models/res_company.py). Runs on
    install only; a later palette change ships as a new version plus a
    migration, so this stays a one-shot rather than rewriting company settings
    on every upgrade.
    """
    env['res.company'].apply_brand_colors()
