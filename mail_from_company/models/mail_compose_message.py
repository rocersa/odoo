from odoo import api, models, tools


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.depends('composition_mode', 'email_from', 'model', 'res_domain', 'res_ids', 'template_id')
    def _compute_authorship(self):
        super()._compute_authorship()
        for composer in self:
            if self.env.context.get('mail_from_company_skip'):
                continue
            # Don't override if a template explicitly sets email_from
            if composer.template_id and composer.template_id.email_from:
                continue
            if not composer.email_from:
                continue

            user_email = tools.email_normalize(self.env.user.email_formatted)
            if not user_email or tools.email_normalize(composer.email_from or '') != user_email:
                continue

            company = self.env.company
            if composer.model and composer.res_ids:
                try:
                    res_ids = composer._evaluate_res_ids()
                    records = self.env[composer.model].browse(res_ids)
                    if hasattr(records, '_mail_get_companies'):
                        # For batch composers, use the first record's company as a reasonable default
                        record_company = records._mail_get_companies(default=company)
                        first_id = records[0].id if records else False
                        if first_id:
                            company = record_company.get(first_id, company)
                except Exception:
                    pass

            if company:
                user_name = self.env.user.name
                email = tools.email_normalize(composer.email_from) or self.env.user.email
                composer.email_from = tools.formataddr((f"{company.name} | {user_name}", email))
