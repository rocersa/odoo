import logging
import smtplib

from odoo import api, models, tools, modules
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.exceptions import UserError

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
        """Override to pass domain_notifications_email context into _connect__
        so that _find_mail_server uses the mail's alias domain instead of
        falling back to the active company's default_from_email."""
        for mail_server_id, alias_domain_id, smtp_from, batch_ids in self._split_by_mail_configuration():
            mail_server = self.env["ir.mail_server"].browse(mail_server_id)

            if mail_server and mail_server.owner_user_id:
                batch_ids = self.browse(batch_ids)._split_by_delayed_batch(mail_server).ids
                if not batch_ids:
                    continue

            smtp_session = None
            try:
                IrMailServer = self.env['ir.mail_server']
                if alias_domain_id:
                    alias_domain = self.env['mail.alias.domain'].sudo().browse(alias_domain_id)
                    IrMailServer = IrMailServer.with_context(
                        domain_notifications_email=alias_domain.default_from_email,
                        domain_bounce_address=alias_domain.bounce_email,
                    )
                    _logger.info(
                        '[mail_from_company] mail.mail send: connecting with alias_domain=%s '
                        'domain_notifications_email=%s for batch_ids=%s',
                        alias_domain.name, alias_domain.default_from_email, batch_ids,
                    )
                else:
                    _logger.info(
                        '[mail_from_company] mail.mail send: no alias_domain_id for batch_ids=%s',
                        batch_ids,
                    )
                smtp_session = IrMailServer._connect__(mail_server_id=mail_server_id, smtp_from=smtp_from)
                _logger.info(
                    '[mail_from_company] mail.mail send: _connect__ returned smtp_from=%s',
                    getattr(smtp_session, 'smtp_from', 'N/A'),
                )
            except Exception as exc:
                if raise_exception:
                    raise MailDeliveryException(_('Unable to connect to SMTP Server'), exc)
                else:
                    batch = self.browse(batch_ids)
                    batch.write({'state': 'exception', 'failure_reason': tools.exception_to_unicode(exc)})
                    batch._postprocess_sent_message(success_pids=[], success_emails=[], failure_type="mail_smtp")
            else:
                self.browse(batch_ids)._send(
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    smtp_session=smtp_session,
                    alias_domain_id=alias_domain_id,
                    mail_server=mail_server,
                    post_send_callback=post_send_callback,
                )
                if not modules.module.current_test:
                    _logger.info(
                        "Processed batch of %s mail.mail records via mail server ID #%s",
                        len(batch_ids), mail_server_id)
            finally:
                if smtp_session:
                    try:
                        smtp_session.quit()
                    except smtplib.SMTPServerDisconnected:
                        _logger.info(
                            "Ignoring SMTPServerDisconnected while trying to quit non open session"
                        )

    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None, alias_domain_id=False,
              mail_server=False, post_send_callback=None):
        for mail in self:
            _logger.info(
                '[mail_from_company] mail.mail _send: id=%s email_from=%s alias_domain=%s state=%s',
                mail.id,
                mail.email_from,
                mail.record_alias_domain_id.name if mail.record_alias_domain_id else 'False',
                mail.state,
            )
        return super()._send(
            auto_commit=auto_commit,
            raise_exception=raise_exception,
            smtp_session=smtp_session,
            alias_domain_id=alias_domain_id,
            mail_server=mail_server,
            post_send_callback=post_send_callback,
        )
