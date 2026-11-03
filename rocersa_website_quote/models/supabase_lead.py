# -*- coding: utf-8 -*-
import logging
import os

import requests

from odoo import api, models

_logger = logging.getLogger(__name__)

PARAM_ENABLED = "rocersa_website_quote.lead_enabled"
PARAM_URL = "rocersa_website_quote.supabase_url"
PARAM_SUBDIVISION = "rocersa_website_quote.subdivision_id"
SERVICE_KEY_ENV = "SUPABASE_SERVICE_KEY"


class WebsiteQuoteLead(models.AbstractModel):
    """Write the shared Supabase ``leads`` row for a website quote request.

    The other storefronts use Supabase ``leads`` as the marketing record; the
    Odoo order is the fulfilment record and stores the returned lead id. The
    write is off by default because it is a live-system write, and it never
    fails the quote: a lost lead is logged and retried on the next attempt.
    """

    _name = "rocersa.website.quote.lead"
    _description = "Supabase lead writer for website quote requests"

    @api.model
    def _config(self):
        params = self.env["ir.config_parameter"].sudo()
        return {
            "enabled": params.get_bool(PARAM_ENABLED, False),
            "url": params.get_str(PARAM_URL, "").rstrip("/"),
            "key": os.environ.get(SERVICE_KEY_ENV, ""),
            "subdivision_id": params.get_int(PARAM_SUBDIVISION, 2),
        }

    @api.model
    def _payload(self, order, client_id=None):
        return {
            "client_id": (client_id or "")[:255],
            "email": order.partner_id.email or "",
            "subdivision_id": self._config()["subdivision_id"],
            "gclid": order.rfq_gclid or None,
            "phone": order.partner_id.phone or None,
        }

    @api.model
    def create_for_order(self, order, client_id=None):
        if not order or order.supabase_lead_id:
            return order.supabase_lead_id if order else False

        config = self._config()
        if not config["enabled"]:
            return False
        if not config["url"] or not config["key"]:
            _logger.warning(
                "Supabase lead write skipped for %s: missing %s or %s",
                order.name,
                PARAM_URL,
                SERVICE_KEY_ENV,
            )
            return False

        payload = self._payload(order, client_id)
        try:
            response = requests.post(
                f"{config['url']}/rest/v1/leads",
                json=payload,
                headers={
                    "apikey": config["key"],
                    "Authorization": f"Bearer {config['key']}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            lead_id = data[0]["id"] if isinstance(data, list) and data else None
            if lead_id is None:
                _logger.warning("Supabase lead write returned no id for %s", order.name)
                return False
            order.sudo().write({"supabase_lead_id": str(lead_id)})
            return lead_id
        except Exception:  # noqa: BLE001 - a lead failure must not fail the RFQ
            _logger.exception("Supabase lead write failed for %s", order.name)
            return False
