import logging

from odoo import models, tools

_logger = logging.getLogger(__name__)


def _trim_company_name(name):
    """Drop the last space-separated token (usually the country code)."""
    parts = (name or '').split()
    if len(parts) > 1:
        return ' '.join(parts[:-1])
    return name or ''


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _message_compute_author(self, author_id=None, email_from=None):
        _logger.info(
            '[mail_from_company] _message_compute_author BEFORE: model=%s res_id=%s author_id=%s email_from=%s',
            self._name, self.id if len(self) == 1 else 'multi', author_id, email_from,
        )
        # Treat falsy email_from as None so the super computes it from the author
        if not email_from:
            email_from = None
        author_id, email_from = super()._message_compute_author(author_id, email_from)
        if (
            len(self) == 1
            and author_id == self.env.user.partner_id.id
            and self.env.user.has_group('base.group_user')
            and not self.env.context.get('mail_from_company_skip')
        ):
            user_email = tools.email_normalize(self.env.user.email_formatted)
            if user_email and tools.email_normalize(email_from or '') == user_email:
                record_company = self._mail_get_companies(default=self.env.company)[self.id]
                if record_company:
                    user_name = self.env.user.name
                    email = tools.email_normalize(email_from) or self.env.user.email
                    if email:
                        company_name = _trim_company_name(record_company.name)
                        email_from = tools.formataddr((f"{company_name} | {user_name}", email))
                _logger.info(
                    '[mail_from_company] _message_compute_author AFTER: model=%s res_id=%s '
                    'record_company=%s email_from=%s',
                    self._name, self.id,
                    record_company.name if record_company else 'False',
                    email_from,
                )
        return author_id, email_from
