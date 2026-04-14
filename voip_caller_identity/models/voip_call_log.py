from odoo import api, fields, models


class VoipCallLog(models.Model):
    _name = "voip.call.log"
    _description = "VoIP Outbound Call Log"
    _order = "call_timestamp desc"

    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        default=lambda self: self.env.user,
    )
    caller_identity_id = fields.Many2one(
        "voip.caller.identity",
        string="Selected Caller Identity",
    )
    resolved_phone_number = fields.Char(
        string="Resolved Caller ID",
        help="The final phone number sent as caller ID",
    )
    dialed_number = fields.Char(string="Dialed Number")
    call_timestamp = fields.Datetime(
        string="Call Time",
        default=fields.Datetime.now,
    )
    validation_result = fields.Selection(
        [
            ("success", "Success"),
            ("fallback_default", "Fallback to Default"),
            ("fallback_system", "Fallback to System Default"),
            ("blocked", "Blocked"),
            ("error", "Error"),
        ],
        string="Validation Result",
    )
    sip_header_method = fields.Char(
        string="SIP Header Method",
        help="Which SIP header was used (e.g. X-Outbound-CallerID, P-Asserted-Identity)",
    )
    note = fields.Text(string="Notes")

    @api.model
    def log_call(self, vals):
        """Create a call log entry from the frontend."""
        return self.create(vals).id
