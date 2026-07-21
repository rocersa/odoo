from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    has_posthog = fields.Boolean(
        "PostHog",
        compute='_compute_has_posthog',
        inverse='_inverse_has_posthog')
    posthog_api_key = fields.Char(related='website_id.posthog_api_key', readonly=False)
    posthog_host = fields.Char(related='website_id.posthog_host', readonly=False)

    @api.depends('website_id')
    def _compute_has_posthog(self):
        for config in self:
            config.has_posthog = bool(config.posthog_api_key)

    def _inverse_has_posthog(self):
        for config in self:
            if not config.has_posthog:
                config.posthog_api_key = False
