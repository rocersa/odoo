import { patch } from '@web/core/utils/patch';
import { WebsiteSale } from '@website_sale/interactions/website_sale';

patch(WebsiteSale.prototype, {
    /**
     * Override _checkExclusions to grey out attribute values that do not
     * participate in any existing variant when restrict_dynamic_variants is
     * enabled on the product template.
     *
     * For select / radio the candidate *replaces* the currently-selected value
     * on its own attribute line so the user can see which other values are
     * available without the old value blocking every option.
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

        // Build a map: attribute-line name → array of currently-selected ptav ids
        const selectedByName = {};
        parent.querySelectorAll('input.js_variant_change:checked, select.js_variant_change').forEach(
            (el) => {
                if (!selectedByName[el.name]) {
                    selectedByName[el.name] = [];
                }
                selectedByName[el.name].push(parseInt(el.value));
            }
        );

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

            // Determine which attribute line this candidate belongs to
            const attrLineName = el.matches('option') ? el.parentElement.name : el.name;
            const isCheckbox = el.matches('input[type="checkbox"]');

            // Build the test combination:
            // - For radio / select: replace the current value on this attribute line
            // - For multi-checkbox: add to the existing selections on this line
            const testCombination = [];
            for (const [name, ptavs] of Object.entries(selectedByName)) {
                if (name === attrLineName) {
                    if (isCheckbox) {
                        testCombination.push(...ptavs, ptavId);
                    } else {
                        testCombination.push(ptavId);
                    }
                } else {
                    testCombination.push(...ptavs);
                }
            }

            const isAvailable = existingCombinations.some((existing) => {
                return testCombination.every((req) => existing.includes(req));
            });

            if (!isAvailable) {
                // Grey out without a tooltip (excludedBy / attributeNames are null)
                this._disableInput(parent, ptavId, null, null);
            }
        });
    },
});
