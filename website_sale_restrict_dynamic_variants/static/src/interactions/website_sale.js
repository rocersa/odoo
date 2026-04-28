import { patch } from '@web/core/utils/patch';
import { WebsiteSale } from '@website_sale/interactions/website_sale';

patch(WebsiteSale.prototype, {
    /**
     * Override _checkExclusions to grey out attribute values that do not
     * participate in any existing variant when restrict_dynamic_variants is
     * enabled on the product template.
     */
    _checkExclusions(parent, combination) {
        super._checkExclusions(parent, combination);

        const combinationDataJson = parent.querySelector('ul[data-attribute-exclusions]')
            ?.dataset.attributeExclusions;
        if (!combinationDataJson) {
            return;
        }

        const combinationData = JSON.parse(combinationDataJson);
        if (!combinationData.restrict_dynamic_variants || !combinationData.existing_combinations) {
            return;
        }

        const existingCombinations = combinationData.existing_combinations;

        // Grey out every unselected input/option that cannot be found in any
        // existing variant together with the currently selected values.
        const allInputs = parent.querySelectorAll(
            'input.js_variant_change, select.css_attribute_select option'
        );

        allInputs.forEach((el) => {
            // Skip elements already excluded by standard rules
            if (el.classList.contains('css_not_available') || el.closest('.css_not_available')) {
                return;
            }

            const ptavId = parseInt(el.value);
            if (isNaN(ptavId)) {
                return;
            }

            // Keep currently-selected values enabled so the user can change away
            if (combination.includes(ptavId)) {
                return;
            }

            const required = [...combination, ptavId];
            const isAvailable = existingCombinations.some((existing) => {
                return required.every((req) => existing.includes(req));
            });

            if (!isAvailable) {
                // Grey out without a tooltip (excludedBy / attributeNames are null)
                this._disableInput(parent, ptavId, null, null);
            }
        });
    },
});
