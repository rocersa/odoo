import logging

from odoo import api, models, tools

_logger = logging.getLogger(__name__)


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
                    _logger.info(
                        '[mail_from_company] composer model=%s res_ids=%s first_id=%s record_company=%s final_company=%s',
                        composer.model, res_ids, first_id,
                        record_company if hasattr(records, '_mail_get_companies') else 'N/A',
                        company.name if company else 'False',
                    )
                except Exception:
                    _logger.exception('[mail_from_company] Failed to resolve record company in composer')

            if company:
                user_name = self.env.user.name
                email = tools.email_normalize(composer.email_from) or self.env.user.email
                composer.email_from = tools.formataddr((f"{company.name} | {user_name}", email))
                _logger.info(
                    '[mail_from_company] composer email_from set to: %s (company=%s)',
                    composer.email_from, company.name,
                )

    @api.depends('composition_mode', 'model', 'res_domain', 'res_ids')
    def _compute_record_environment(self):
        super()._compute_record_environment()
        for composer in self.filtered(lambda comp: not comp.composition_batch):
            res_ids = composer._evaluate_res_ids()
            if composer.model in self.env and len(res_ids) == 1:
                record = self.env[composer.model].browse(res_ids)
                record_company = record._mail_get_companies(default=self.env.company)[record.id]
                alias_domain = record._mail_get_alias_domains(default_company=record_company)[record.id]
                composer.record_alias_domain_id = alias_domain.id if alias_domain else False
                _logger.info(
                    '[mail_from_company] record_environment: model=%s res_id=%s '
                    'record_company=%s alias_domain=%s (id=%s)',
                    composer.model, record.id,
                    record_company.name if record_company else 'False',
                    alias_domain.name if alias_domain else 'False',
                    alias_domain.id if alias_domain else 'False',
                )
