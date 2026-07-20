import os
import time

from odoo import api, models
from odoo.addons.base.models.ir_http import EXTENSION_TO_WEB_MIMETYPES

from .website import (
    POSTHOG_DISTINCT_ID_COOKIE,
    POSTHOG_DISTINCT_ID_COOKIE_MAX_AGE,
)


class WebsitePage(models.Model):
    _inherit = 'website.page'

    def _get_active_posthog_experiment(self):
        """The active experiment using this page as its base page, if any."""
        self.ensure_one()
        experiment_id = self.env['website.experiment']._get_experiment_id_for_page(self.id)
        return self.env['website.experiment'].sudo().browse(experiment_id or [])

    # website cache

    @api.model
    def _allow_to_use_cache(self, request):
        # never cache a page that is the base of an active experiment: the
        # variant to serve is decided per visitor
        if len(self) == 1 and self._get_active_posthog_experiment():
            return False
        return super()._allow_to_use_cache(request)

    def _get_response_raw(self, request):
        # website designers always get the control page, so the builder and
        # page previews are never affected by experiments
        if (
            len(self) == 1
            and not request.env.user.has_group('website.group_website_designer')
            and (experiment := self._get_active_posthog_experiment())
            and (variant_value := request.website._get_posthog_flag_variant(
                request, experiment.flag_key))
        ):
            request.posthog_experiment = {
                'flag_key': experiment.flag_key,
                'variant_value': variant_value,
                'distinct_id': request.website._get_posthog_distinct_id(request),
            }
            variant = experiment.variant_ids.filtered(
                lambda v: v.key == variant_value)[:1]
            if variant:
                response = self._render_posthog_variant(request, variant.page_id)
            else:
                # variant key known to PostHog but without a page (e.g.
                # 'control') -> serve the base page, still tracked
                response = super()._get_response_raw(request)
        else:
            response = super()._get_response_raw(request)

        new_distinct_id = getattr(request, 'posthog_new_distinct_id', None)
        if response and new_distinct_id:
            response.set_cookie(
                POSTHOG_DISTINCT_ID_COOKIE,
                new_distinct_id,
                max_age=POSTHOG_DISTINCT_ID_COOKIE_MAX_AGE,
            )
        return response

    def _render_posthog_variant(self, request, variant_page):
        """Render the variant's view under the base page URL.

        The accessibility gate below mirrors `website.page._get_response_raw`
        (we bypass it by rendering the variant's view directly instead of the
        base page's view).
        """
        self.ensure_one()
        if (
            (self.env.user.has_group('website.group_website_designer') or self.is_visible)
            and (
                self.website_id
                or self.view_id.id == self.env['ir.ui.view']
                    .with_context(website_id=request.website.id)
                    ._get_cached_template_info(self.view_id.key)['id']
            )
        ):
            _, ext = os.path.splitext(request.httprequest.path)
            response = request.render(variant_page.view_id.id, {
                'main_object': self,
            }, mimetype=EXTENSION_TO_WEB_MIMETYPES.get(ext, 'text/html'))
            response.time = time.time()
            return response
        return None
