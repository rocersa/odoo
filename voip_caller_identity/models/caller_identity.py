import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VoipCallerIdentity(models.Model):
    _name = "voip.caller.identity"
    _description = "Outbound Caller Identity"
    _order = "sequence, name"

    name = fields.Char(
        string="Label",
        required=True,
        help="Display label, e.g. 'AU Sales', 'Corten Brand', 'UK Support'",
    )
    phone_number = fields.Char(
        string="Phone Number (E.164)",
        required=True,
        help="Phone number in E.164 format, e.g. +61291234567",
    )
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        help="Country/region associated with this caller identity",
    )
    business_unit = fields.Char(
        string="Business Unit",
        help="Associated business unit, e.g. Gabion1, Corten",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    user_ids = fields.Many2many(
        "res.users",
        "voip_caller_identity_user_rel",
        "identity_id",
        "user_id",
        string="Allowed Users",
    )
    team_ids = fields.Many2many(
        "crm.team",
        "voip_caller_identity_team_rel",
        "identity_id",
        "team_id",
        string="Allowed Teams",
    )
    note = fields.Text(string="Notes")

    _E164_PATTERN = re.compile(r"^\+[1-9]\d{1,14}$")

    @api.constrains("phone_number")
    def _check_phone_number_format(self):
        for rec in self:
            if rec.phone_number and not self._E164_PATTERN.match(rec.phone_number):
                raise ValidationError(
                    f"Phone number '{rec.phone_number}' must be in E.164 format "
                    "(e.g. +61291234567)."
                )

    @api.depends("name", "phone_number")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name} ({rec.phone_number})"

    @api.model
    def get_allowed_identities(self):
        """Return caller identities allowed for the current user, for the JS frontend."""
        user = self.env.user
        domain = [
            ("active", "=", True),
            "|",
            "|",
            ("user_ids", "=", False),
            ("user_ids", "in", user.id),
            "|",
            ("team_ids", "=", False),
            ("team_ids", "in", user.sale_team_id.id if user.sale_team_id else 0),
        ]
        if user.company_id:
            domain = [("company_id", "in", [user.company_id.id, False])] + domain
        identities = self.search(domain)
        return [
            {
                "id": identity.id,
                "name": identity.name,
                "phone_number": identity.phone_number,
                "country_code": identity.country_id.code if identity.country_id else False,
                "business_unit": identity.business_unit or False,
            }
            for identity in identities
        ]

    @api.model
    def validate_identity_for_user(self, identity_id):
        """Validate that the current user is allowed to use the given identity."""
        if not identity_id:
            return {"valid": False, "reason": "no_identity"}
        identity = self.browse(identity_id).exists()
        if not identity:
            return {"valid": False, "reason": "not_found"}
        if not identity.active:
            return {"valid": False, "reason": "inactive"}
        allowed = self.get_allowed_identities()
        allowed_ids = [a["id"] for a in allowed]
        if identity.id not in allowed_ids:
            return {"valid": False, "reason": "not_allowed"}
        return {
            "valid": True,
            "phone_number": identity.phone_number,
            "name": identity.name,
            "identity_id": identity.id,
        }
