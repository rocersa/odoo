import logging

from odoo import models, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    restrict_dynamic_variants = fields.Boolean(
        string="Restrict to Existing Variants",
        help=(
            "If set, customers can only select attribute combinations that "
            "already have an active variant. The add-to-cart button is disabled "
            "for missing combinations and Odoo will not create new variants on demand."
        ),
    )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _should_filter_by_website(self):
        """Return True when we are in a website/frontend request context."""
        return bool(request and getattr(request, 'is_frontend', False))

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
        """Mark missing or invisible combinations as impossible when restriction is enabled."""
        possible = super()._is_combination_possible(
            combination, parent_combination=parent_combination, ignore_no_variant=ignore_no_variant
        )
        if not possible:
            return False

        if self.restrict_dynamic_variants:
            variant = self._get_variant_for_combination(combination)
            if not variant or not variant.active:
                return False
            if self._should_filter_by_website() and hasattr(variant, 'is_visible_on_current_website'):
                if not variant.is_visible_on_current_website():
                    return False

        return True

    # -------------------------------------------------------------------------
    # Attribute exclusions (feeds the frontend exclusion data)
    # -------------------------------------------------------------------------

    def _get_attribute_exclusions(self, parent_combination=None, parent_name=None, combination_ids=None):
        """Add existing-combination data so the JS can grey out missing variants."""
        res = super()._get_attribute_exclusions(
            parent_combination=parent_combination,
            parent_name=parent_name,
            combination_ids=combination_ids,
        )
        if self.restrict_dynamic_variants:
            res['restrict_dynamic_variants'] = True
            res['existing_combinations'] = [
                tuple(product.product_template_attribute_value_ids.ids)
                for product in self._get_visible_variants()
                if product.product_template_attribute_value_ids
            ]
        return res

    # -------------------------------------------------------------------------
    # Variant creation choke-point
    # -------------------------------------------------------------------------

    def _create_product_variant(self, combination, log_warning=False):
        """Refuse to create new variants when restriction is enabled.

        This blocks on-the-fly creation from:
        - website_sale (add to cart, media updates)
        - sale product configurator
        - point_of_sale
        - sale/purchase matrix
        """
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
            if self._should_filter_by_website() and hasattr(variant, 'is_visible_on_current_website'):
                if not variant.is_visible_on_current_website():
                    if log_warning:
                        _logger.warning(
                            "Dynamic variant creation blocked for template %s (id=%s) "
                            "because the variant is not visible on the current website.",
                            self.name, self.id,
                        )
                    return self.env['product.product']
            return variant

        return super()._create_product_variant(combination, log_warning=log_warning)
