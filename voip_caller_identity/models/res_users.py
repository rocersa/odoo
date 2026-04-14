from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    voip_caller_identity_ids = fields.Many2many(
        "voip.caller.identity",
        "voip_caller_identity_user_rel",
        "user_id",
        "identity_id",
        string="Allowed Caller Identities",
    )
    voip_default_caller_identity_id = fields.Many2one(
        "voip.caller.identity",
        string="Default Caller Identity",
        domain="[('id', 'in', voip_caller_identity_ids)]",
        help="Default outbound caller identity for this user",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            "voip_caller_identity_ids",
            "voip_default_caller_identity_id",
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            "voip_default_caller_identity_id",
        ]
