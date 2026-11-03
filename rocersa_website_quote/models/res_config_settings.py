# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_disable_checkout = fields.Boolean(
        string="Quote Mode",
        related="website_id.is_disable_checkout",
        readonly=False,
        help="Hide the checkout button and replace it with a quote-request "
             "button on the cart page of this website.",
    )

    website_quote_lead_enabled = fields.Boolean(
        string="Write quote requests to Supabase",
        config_parameter="rocersa_website_quote.lead_enabled",
        help="Create the shared Supabase leads row for each quote request. "
             "The Odoo order stays the fulfilment record and stores the "
             "returned lead id. Off by default because this writes live data.",
    )
    website_quote_supabase_url = fields.Char(
        string="Supabase URL",
        config_parameter="rocersa_website_quote.supabase_url",
        help="Project URL, e.g. https://xxxx.supabase.co. The service key is "
             "read from the SUPABASE_SERVICE_KEY environment variable and is "
             "never stored in the database.",
    )
    website_quote_subdivision_id = fields.Integer(
        string="Lead subdivision",
        config_parameter="rocersa_website_quote.subdivision_id",
        default=2,
        help="Supabase subdivisions.id for this website. AU Corten is 2.",
    )
    website_quote_posthog_enabled = fields.Boolean(
        string="Send quote_request_submitted to PostHog",
        config_parameter="rocersa_website_quote.posthog_event_enabled",
        help="Send the quote event with the website's PostHog project key "
             "and host. Off by default because it writes live analytics data.",
    )
