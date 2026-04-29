import logging

from odoo import models, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    restrict_dynamic_variants = fields.Boolean(
        string="Restrict to Existing Variants",
        help=(
            "If set, backend users (sale configurator, POS, matrix, etc.) can "
            "only select attribute combinations that already have an active variant. "
            "The website storefront always filters by visible variants regardless of this setting."
        ),
    )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _should_filter_by_website(self):
        """Return True when we are in a website/frontend request context."""
        if self.env.context.get('website_id'):
            return True
        if not request:
            return False
        if getattr(request, 'is_frontend', False):
            return True
        if hasattr(request, 'website') and request.website:
            return True
        return False

    def _get_visible_variants(self):
        """Return variants that are active and visible on the current website."""
        variants = self.product_variant_ids.filtered('active')
        if self._should_filter_by_website() and hasattr(variants, 'is_visible_on_current_website'):
            variants = variants.filtered(lambda p: p.is_visible_on_current_website())
        return variants

    # -------------------------------------------------------------------------
    # Combination possibility
    # -------------------------------------------------------------------------

    def _is_combination_possible(self, combination, parent_combination=None, ignore_no_variant=False):
        """Mark missing or invisible combinations as impossible.

        On the website this always applies.  In the backend it only applies
        when restrict_dynamic_variants is enabled.
        """
        possible = super()._is_combination_possible(
            combination, parent_combination=parent_combination, ignore_no_variant=ignore_no_variant
        )
        if not possible:
            return False

        # Website: always enforce visibility
        if self._should_filter_by_website():
            variant = self._get_variant_for_combination(combination)
            if not variant or not variant.active:
                return False
            if hasattr(variant, 'is_visible_on_current_website'):
                if not variant.is_visible_on_current_website():
                    return False
            return True

        # Backend: only enforce when the flag is set
        if self.restrict_dynamic_variants:
            variant = self._get_variant_for_combination(combination)
            if not variant or not variant.active:
                return False

        return True

    # -------------------------------------------------------------------------
    # Attribute exclusions (feeds the frontend exclusion data)
    # -------------------------------------------------------------------------

    def _get_attribute_exclusions(self, parent_combination=None, parent_name=None, combination_ids=None):
        """Add existing-combination data so the JS can grey out missing variants.

        On the website this always runs; in the backend it only runs when
        restrict_dynamic_variants is enabled.
        """
        res = super()._get_attribute_exclusions(
            parent_combination=parent_combination,
            parent_name=parent_name,
            combination_ids=combination_ids,
        )

        # Only inject our data when we're on the website or when backend restriction is on
        if self._should_filter_by_website() or self.restrict_dynamic_variants:
            visible_variants = self._get_visible_variants()
            res['existing_combinations'] = [
                tuple(product.product_template_attribute_value_ids.ids)
                for product in visible_variants
                if product.product_template_attribute_value_ids
            ]
            # Signal the JS that it should run our grey-out logic
            res['restrict_dynamic_variants'] = True

        return res

    # -------------------------------------------------------------------------
    # Variant creation choke-point
    # -------------------------------------------------------------------------

    def _create_product_variant(self, combination, log_warning=False):
        """Refuse to create new variants when restriction is enabled.

        On the website this always blocks invisible/missing variants.
        In the backend it only blocks when restrict_dynamic_variants is set.
        """
        # Website: always restrict to existing visible variants
        if self._should_filter_by_website():
            variant = self._get_variant_for_combination(combination)
            if not variant:
                if log_warning:
                    _logger.warning(
                        "Variant creation blocked on website for template %s (id=%s): "
                        "combination does not exist.",
                        self.name, self.id,
                    )
                return self.env['product.product']
            if not variant.active:
                if log_warning:
                    _logger.warning(
                        "Variant creation blocked on website for template %s (id=%s): "
                        "variant is archived.",
                        self.name, self.id,
                    )
                return self.env['product.product']
            if hasattr(variant, 'is_visible_on_current_website'):
                if not variant.is_visible_on_current_website():
                    if log_warning:
                        _logger.warning(
                            "Variant creation blocked on website for template %s (id=%s): "
                            "variant is not visible on current website.",
                            self.name, self.id,
                        )
                    return self.env['product.product']
            return variant

        # Backend: restrict only if the flag is set
        if self.restrict_dynamic_variants:
            variant = self._get_variant_for_combination(combination)
            if not variant:
                if log_warning:
                    _logger.warning(
                        "Dynamic variant creation blocked for template %s (id=%s) "
                        "because restrict_dynamic_variants is enabled.",
                        self.name, self.id,
                    )
                return self.env['product.product']
            if not variant.active:
                return self.env['product.product']
            return variant

        return super()._create_product_variant(combination, log_warning=log_warning)
