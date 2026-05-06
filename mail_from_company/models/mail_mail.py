import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            mail_message_id = values.get('mail_message_id')
            if not mail_message_id:
                continue
            message = self.env['mail.message'].browse(mail_message_id)
            # Explicitly copy email_from from the parent message to avoid
            # relying solely on _inherits, which can leave the field falsy
            # in some Odoo versions / contexts and cause fallback to the
            # active company's catchall address.
            if not values.get('email_from') and message.email_from:
                values['email_from'] = message.email_from
            # Also ensure record_alias_domain_id is carried over so the mail
            # server fallback uses the record's alias domain rather than the
            # active company's.
            if not values.get('record_alias_domain_id') and message.record_alias_domain_id:
                values['record_alias_domain_id'] = message.record_alias_domain_id.id
            _logger.info(
                '[mail_from_company] mail.mail create: msg_id=%s msg_email_from=%s '
                'msg_alias_domain=%s -> mail_email_from=%s mail_alias_domain=%s',
                mail_message_id,
                message.email_from,
                message.record_alias_domain_id.name if message.record_alias_domain_id else 'False',
                values.get('email_from'),
                values.get('record_alias_domain_id'),
            )
        return super().create(vals_list)

    def send(self, auto_commit=False, raise_exception=False, post_send_callback=None):
        for mail in self:
            _logger.info(
                '[mail_from_company] mail.mail send: id=%s email_from=%s alias_domain=%s state=%s',
                mail.id,
                mail.email_from,
                mail.record_alias_domain_id.name if mail.record_alias_domain_id else 'False',
                mail.state,
            )
        return super().send(
            auto_commit=auto_commit,
            raise_exception=raise_exception,
            post_send_callback=post_send_callback,
        )
