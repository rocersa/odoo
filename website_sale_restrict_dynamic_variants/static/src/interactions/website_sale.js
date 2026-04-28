import { patch } from "@web/core/utils/patch";
import { WebsiteSale } from "@website_sale/js/website_sale";

/**
 * Patch the WebsiteSale interaction to grey out unavailable variant combinations
 * when the template restricts variants to existing ones only.
 */
patch(WebsiteSale.prototype, {
    /**
     * @override
     * After Odoo's standard exclusion check, additionally disable any option that
     * does not participate in at least one existing visible variant.
     */
    _checkExclusions(parent, combination) {
        // Let Odoo do its normal exclusions first.
        super._checkExclusions(parent, combination);

        const combinationDataJson = parent.querySelector('ul[data-attribute-exclusions]')
            ?.dataset.attributeExclusions;
        if (!combinationDataJson) {
            return;
        }
        const combinationData = JSON.parse(combinationDataJson);
        if (!combinationData.existing_combinations) {
            return;
        }

        const existingCombinations = combinationData.existing_combinations;

        // Build a map of currently-selected values grouped by attribute line name.
        const selectedByName = {};
        parent.querySelectorAll('input.js_variant_change:checked, select.js_variant_change').forEach(
            (el) => {
                if (!selectedByName[el.name]) {
                    selectedByName[el.name] = [];
                }
                selectedByName[el.name].push(parseInt(el.value));
            }
        );

        // Reset disabled state on all inputs so we can re-evaluate after changes.
        const allInputs = parent.querySelectorAll(
            'input.js_variant_change, select.css_attribute_select option'
        );
        allInputs.forEach((el) => {
            el.disabled = false;
        });

        allInputs.forEach((el) => {
            // If the option is already excluded by Odoo's standard rules, mark it
            // disabled and skip further checks.
            if (el.classList.contains('css_not_available') || el.closest('.css_not_available')) {
                el.disabled = true;
                return;
            }

            const ptavId = parseInt(el.value);
            if (isNaN(ptavId) || combination.includes(ptavId)) {
                return;
            }

            const attrLineName = el.matches('option') ? el.parentElement.name : el.name;
            const isCheckbox = el.matches('input[type="checkbox"]');

            // Build a test combination where this option is selected on its attribute line.
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

            // Only keep this option if the test combination is a subset of at
            // least one existing visible variant.
            const isAvailable = existingCombinations.some((existing) => {
                return testCombination.every((req) => existing.includes(req));
            });

            if (!isAvailable) {
                // Force Odoo's CSS class for visual grey-out.
                this._disableInput(parent, ptavId, null, null);
                // Also make it un-interactive.
                el.disabled = true;
            }
        });
    },
});
