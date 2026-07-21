from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class WebsiteExperiment(models.Model):
    _name = 'website.experiment'
    _description = 'Website A/B Experiment'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    flag_key = fields.Char(
        'PostHog Feature Flag Key',
        required=True,
        help="Key of the multivariate feature flag in PostHog that drives this "
             "experiment. Variant keys below must match the flag's variant keys "
             "in PostHog ('control' always serves the base page).",
    )
    base_page_id = fields.Many2one(
        'website.page',
        string='Base (Control) Page',
        required=True,
        ondelete='cascade',
    )
    website_id = fields.Many2one(
        'website',
        related='base_page_id.website_id',
        store=True,
        readonly=True,
    )
    base_url = fields.Char(related='base_page_id.url', readonly=True)
    variant_ids = fields.One2many(
        'website.experiment.variant',
        'experiment_id',
        string='Variants',
        copy=True,
    )

    @api.model
    @tools.ormcache('page_id')
    def _get_experiment_id_for_page(self, page_id):
        experiment = self.sudo().search_fetch(
            [('base_page_id', '=', page_id), ('active', '=', True)], ['id'], limit=1)
        return experiment.id or None

    def action_create_variant(self):
        """Duplicate the base page as a new (unpublished) variant and open it
        in a new tab so it can be edited in the website builder."""
        self.ensure_one()
        existing_keys = set(self.variant_ids.mapped('key'))
        key = 'test'
        index = 1
        while key in existing_keys:
            index += 1
            key = f'test-{index}'
        variant_page = self.base_page_id.copy({
            'name': f"{self.base_page_id.name} - {key}",
            # keep the variant specific to the same website: editing it in
            # the builder then writes directly to its view instead of COWing
            # a generic view into a separate website-specific copy
            'website_id': self.base_page_id.website_id.id,
        })
        variant_page.is_published = False
        self.env['website.experiment.variant'].create({
            'experiment_id': self.id,
            'key': key,
            'page_id': variant_page.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': variant_page.url,
            'target': 'new',
        }


class WebsiteExperimentVariant(models.Model):
    _name = 'website.experiment.variant'
    _description = 'Website Experiment Variant'
    _order = 'experiment_id, key'

    experiment_id = fields.Many2one(
        'website.experiment', required=True, ondelete='cascade')
    key = fields.Char(
        required=True,
        help="Variant key as configured on the PostHog feature flag, e.g. 'test'.")
    page_id = fields.Many2one(
        'website.page', string='Variant Page', required=True, ondelete='cascade')
    page_url = fields.Char(related='page_id.url', readonly=True)
    is_published = fields.Boolean(related='page_id.is_published', readonly=False)

    _key_unique_per_experiment = models.Constraint(
        'unique(experiment_id, key)',
        'Each variant key can only be used once per experiment.',
    )

    @api.constrains('experiment_id', 'page_id')
    def _check_page_is_not_base_page(self):
        for variant in self:
            if variant.page_id and variant.page_id == variant.experiment_id.base_page_id:
                raise ValidationError(_(
                    "The variant page must be different from the base (control) page."))
