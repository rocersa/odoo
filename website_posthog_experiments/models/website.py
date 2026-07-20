import json
import logging
import uuid

import requests
from markupsafe import Markup

from odoo import fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

POSTHOG_DISTINCT_ID_COOKIE = 'wph_distinct_id'
POSTHOG_DISTINCT_ID_COOKIE_MAX_AGE = 365 * 24 * 3600
POSTHOG_DEFAULT_HOST = 'https://us.i.posthog.com'
POSTHOG_FLAGS_TIMEOUT = 2


class Website(models.Model):
    _inherit = 'website'

    posthog_api_key = fields.Char('PostHog Project API Key')
    posthog_host = fields.Char(
        'PostHog Host',
        default=POSTHOG_DEFAULT_HOST,
        help="Base URL of your PostHog instance, e.g. https://us.i.posthog.com "
             "https://eu.i.posthog.com or your self-hosted URL.",
    )

    def _get_posthog_distinct_id(self, request):
        """Return the visitor's stable distinct id, from the cookie if present.

        When a new id is generated it is stashed on the request so that the
        response (`website.page._get_response_raw`) can persist it as a cookie.
        """
        distinct_id = request.httprequest.cookies.get(POSTHOG_DISTINCT_ID_COOKIE)
        if not distinct_id:
            distinct_id = str(uuid.uuid4())
            request.posthog_new_distinct_id = distinct_id
        return distinct_id

    def _get_posthog_flag_variant(self, request, flag_key):
        """Evaluate a PostHog feature flag for the current visitor.

        Returns the variant key (string) or None when the flag does not apply
        (PostHog unreachable, flag disabled, visitor outside the rollout...),
        in which case the caller serves the control page. Results are cached
        in the visitor session to avoid one HTTP call per page view.
        """
        self.ensure_one()
        if not self.posthog_api_key:
            return None
        flags = dict(request.session.get('posthog_flags') or {})
        if flag_key not in flags:
            distinct_id = self._get_posthog_distinct_id(request)
            host = (self.posthog_host or POSTHOG_DEFAULT_HOST).rstrip('/')
            try:
                response = requests.post(
                    f"{host}/flags?v=2",
                    json={'api_key': self.posthog_api_key, 'distinct_id': distinct_id},
                    timeout=POSTHOG_FLAGS_TIMEOUT,
                )
                response.raise_for_status()
                flags.update(response.json().get('featureFlags') or {})
            except Exception:
                _logger.warning(
                    "PostHog flag evaluation failed, serving control page", exc_info=True)
                return None
            # remember "flag not returned" too, so we don't re-call per page view
            flags.setdefault(flag_key, None)
            request.session['posthog_flags'] = flags
        value = flags.get(flag_key)
        # multivariate flags return the variant key as a string; boolean flags
        # and missing flags are treated as "no variant" -> control
        return value if isinstance(value, str) else None

    def _get_posthog_frontend_context(self):
        """Data consumed by the PostHog snippet in `website.layout`.

        Returns None outside of a frontend request. `bootstrap_json` is a
        pre-serialized posthog-js `bootstrap` config so the client SDK uses
        the same distinct id and flag values that the server rendered with,
        and `flag_key` triggers the `$feature_flag_called` exposure event.
        """
        if not request:
            return None
        experiment = getattr(request, 'posthog_experiment', None)
        return {
            'flag_key': experiment['flag_key'] if experiment else None,
            'bootstrap_json': Markup(json.dumps({
                'distinctID': experiment['distinct_id'],
                'featureFlags': {experiment['flag_key']: experiment['variant_value']},
            })) if experiment else None,
        }
