# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_rfq_from_website = fields.Boolean(string="Request from Website")
    rfq_message = fields.Text(string="Quote Request Message")
    rfq_company = fields.Char(string="Quote Company")
    rfq_gclid = fields.Char(string="Google Click ID")
    rfq_utm_source = fields.Char(string="UTM Source")
    rfq_utm_medium = fields.Char(string="UTM Medium")
    rfq_utm_campaign = fields.Char(string="UTM Campaign")
    rfq_landing_page = fields.Char(string="Landing Page")
    supabase_lead_id = fields.Char(
        string="Supabase Lead ID", readonly=True, copy=False, index=True
    )

    def _apply_website_rfq(self, partner, message=None, attribution=None, company=None):
        """Attach the quote contact, flag the cart as an RFQ and send it.

        ``partner`` is either the logged-in user's partner or a new contact
        created from the guest form. The order is written with sudo because the
        public user owns the cart; the partner is never modified here.
        """
        self.ensure_one()
        values = {
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": partner.id,
            "is_rfq_from_website": True,
            "rfq_message": message or False,
            "rfq_company": company or False,
        }
        allowed = {
            "rfq_gclid",
            "rfq_utm_source",
            "rfq_utm_medium",
            "rfq_utm_campaign",
            "rfq_landing_page",
        }
        for key, value in (attribution or {}).items():
            if key in allowed and value:
                values[key] = value
        self.sudo().write(values)
        if message:
            self.sudo().message_post(body=message, subtype_xmlid="mail.mt_note")
        self.sudo().action_quotation_sent()
        return self
