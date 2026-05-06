from odoo import api, models, tools


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if (
                ('email_from' not in values or not values.get('email_from'))
                and values.get('model')
                and values.get('res_id')
                and not self._context.get('mail_from_company_skip')
                and self.env.user.has_group('base.group_user')
            ):
                author_id = values.get('author_id')
                if author_id and author_id != self.env.user.partner_id.id:
                    continue
                try:
                    record = self.env[values['model']].browse(values['res_id'])
                    if hasattr(record, '_mail_get_companies'):
                        company = record._mail_get_companies(default=self.env.company)[record.id]
                        if company:
                            user_name = self.env.user.name
                            email = tools.email_normalize(self.env.user.email_formatted) or self.env.user.email
                            values['email_from'] = tools.formataddr((f"{company.name} | {user_name}", email))
                except Exception:
                    pass
        return super().create(vals_list)
