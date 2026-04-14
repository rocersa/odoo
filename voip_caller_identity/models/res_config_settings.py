from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    voip_sip_header_name = fields.Char(
        string="SIP Header Name",
        config_parameter="voip_caller_identity.sip_header_name",
        default="X-Outbound-CallerID",
        help="Custom SIP header name used to pass caller identity to FreePBX",
    )
    voip_sip_header_format = fields.Selection(
        [
            ("number_only", "Phone Number Only"),
            ("number_and_label", "Phone Number + Label"),
            ("sip_uri", "SIP URI Format"),
        ],
        string="SIP Header Format",
        config_parameter="voip_caller_identity.sip_header_format",
        default="number_only",
        help="Format of the value sent in the SIP header",
    )
    voip_identity_fallback = fields.Selection(
        [
            ("user_default", "Use User Default"),
            ("system_default", "Use System Default"),
            ("block", "Block Call"),
        ],
        string="Missing Identity Behaviour",
        config_parameter="voip_caller_identity.fallback_behaviour",
        default="user_default",
        help="What to do when no caller identity is selected",
    )
    voip_invalid_identity_action = fields.Selection(
        [
            ("fallback", "Fallback to Default"),
            ("block", "Block Call"),
        ],
        string="Invalid Identity Behaviour",
        config_parameter="voip_caller_identity.invalid_identity_action",
        default="fallback",
        help="What to do when the selected identity is invalid",
    )
    voip_system_default_identity_id = fields.Many2one(
        "voip.caller.identity",
        string="System Default Caller Identity",
        config_parameter="voip_caller_identity.system_default_identity_id",
        help="Fallback identity when no user/team default is set",
    )
