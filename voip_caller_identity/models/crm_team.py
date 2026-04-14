from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    voip_caller_identity_ids = fields.Many2many(
        "voip.caller.identity",
        "voip_caller_identity_team_rel",
        "team_id",
        "identity_id",
        string="Allowed Caller Identities",
    )
    voip_default_caller_identity_id = fields.Many2one(
        "voip.caller.identity",
        string="Default Caller Identity",
        domain="[('id', 'in', voip_caller_identity_ids)]",
        help="Default outbound caller identity for this team",
    )
