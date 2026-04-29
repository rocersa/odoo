from odoo import models, tools


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _message_compute_author(self, author_id=None, email_from=None):
        author_id, email_from = super()._message_compute_author(author_id, email_from)
        if (
            len(self) == 1
            and author_id == self.env.user.partner_id.id
            and self.env.user.has_group('base.group_user')
            and not self._context.get('mail_from_company_skip')
        ):
            user_email = tools.email_normalize(self.env.user.email_formatted)
            if user_email and tools.email_normalize(email_from or '') == user_email:
                record_company = self._mail_get_companies(default=self.env.company)[self.id]
                if record_company:
                    user_name = self.env.user.name
                    email = tools.email_normalize(email_from) or self.env.user.email
                    email_from = tools.formataddr((f"{record_company.name} | {user_name}", email))
        return author_id, email_from
