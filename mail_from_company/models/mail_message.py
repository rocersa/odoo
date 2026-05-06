import logging

from odoo import api, models, tools

_logger = logging.getLogger(__name__)


def _trim_company_name(name):
    """Drop the last space-separated token (usually the country code)."""
    parts = (name or '').split()
    if len(parts) > 1:
        return ' '.join(parts[:-1])
    return name or ''


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            has_email_from = 'email_from' in values
            email_from_val = values.get('email_from')
            if (
                ('email_from' not in values or not values.get('email_from'))
                and values.get('model')
                and values.get('res_id')
                and not self.env.context.get('mail_from_company_skip')
                and self.env.user.has_group('base.group_user')
            ):
                author_id = values.get('author_id')
                if author_id and author_id != self.env.user.partner_id.id:
                    _logger.info(
                        '[mail_from_company] mail.message skipping: author_id=%s != user.partner_id=%s',
                        author_id, self.env.user.partner_id.id,
                    )
                    continue
                try:
                    record = self.env[values['model']].browse(values['res_id'])
                    if hasattr(record, '_mail_get_companies'):
                        company = record._mail_get_companies(default=self.env.company)[record.id]
                        if company:
                            user_name = self.env.user.name
                            email = tools.email_normalize(self.env.user.email_formatted) or self.env.user.email
                            company_name = _trim_company_name(company.name)
                            values['email_from'] = tools.formataddr((f"{company_name} | {user_name}", email))
                            _logger.info(
                                '[mail_from_company] mail.message create: model=%s res_id=%s '
                                'company=%s email_from=%s',
                                values['model'], values['res_id'], company.name, values['email_from'],
                            )
                except Exception:
                    _logger.exception('[mail_from_company] mail.message create failed to compute email_from')
            else:
                _logger.info(
                    '[mail_from_company] mail.message create skipping: has_email_from=%s email_from_val=%s model=%s res_id=%s',
                    has_email_from, email_from_val, values.get('model'), values.get('res_id'),
                )
        return super().create(vals_list)
