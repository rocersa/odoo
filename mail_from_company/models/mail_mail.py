from odoo import api, models


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
        return super().create(vals_list)
