"""Consent state for the UK websites.

Odoo's own `_allConsentsGranted()` returns True when `cookies_bar` is off — its
comment says it assumes the operator implemented their own consent. The UK
sites kept the cookies bar off, so the core Google block auto-granted on every
first visit. This module supplies the custom consent the core assumed: an
apex-domain `rocersa_consent` cookie written by the banner in
`static/src/js/consent.js` (shared with the products subdomain).

Non-UK websites keep Odoo's behaviour: consent is considered granted, so AU/NZ/
US tracking is unconditional exactly as before.
"""
from odoo import models
from odoo.http import request


def _optional_granted(raw):
    """`v1:<analytics>:<marketing>:<ts>` — granted when both optional flags are 1."""
    if not raw:
        return False
    parts = raw.split(":")
    return len(parts) == 4 and parts[0] == "v1" and parts[1] == "1" and parts[2] == "1"


class Website(models.Model):
    _inherit = "website"

    def _is_uk(self):
        self.ensure_one()
        return self.company_id.country_id.code == "GB"

    def _allConsentsGranted(self):
        self.ensure_one()
        if not self._is_uk():
            return True
        try:
            raw = request.httprequest.cookies.get("rocersa_consent")
        except Exception:  # no request context (cron, CLI)
            raw = None
        return _optional_granted(raw)
