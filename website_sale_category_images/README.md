# Website Sale Category Images

## Overview

Add images at the **Ecommerce Category** level that automatically appear in the product image carousel for every product belonging to that category. This allows bulk-updating generic/lifestyle images for an entire category without touching individual products.

---

## Current System (Odoo `website_sale`)

### How product images are stored

| Model              | Field(s)                                                           | Purpose                                                        |
| ------------------ | ------------------------------------------------------------------ | -------------------------------------------------------------- |
| `product.template` | `image_1920` (from `image.mixin`)                                  | Main product image                                             |
| `product.product`  | `image_1920` (from `image.mixin`)                                  | Variant-specific main image (falls back to template)           |
| `product.image`    | `image_1920`, `video_url`, `product_tmpl_id`, `product_variant_id` | Extra images/videos linked to a template or a specific variant |

- `product.template` has a One2many `product_template_image_ids` → `product.image` (extra images for the template).
- `product.product` has a One2many `product_variant_image_ids` → `product.image` (extra images for a specific variant).

### How images are collected for the carousel

Both `product.template` and `product.product` implement a `_get_images()` method that returns a list of records (implementing `image.mixin`) to display in the carousel.

**`product.template._get_images()`** (`odoo/addons/website_sale/models/product_template.py`):

```python
def _get_images(self):
    self.ensure_one()
    return [self] + list(self.product_template_image_ids)
```

Returns: `[template_main_image, *template_extra_images]`

**`product.product._get_images()`** (`odoo/addons/website_sale/models/product_product.py`):

```python
def _get_images(self):
    self.ensure_one()
    variant_images = list(self.product_variant_image_ids)
    template_images = list(self.product_tmpl_id.product_template_image_ids)
    return [self] + variant_images + template_images
```

Returns: `[variant_main_image, *variant_extra_images, *template_extra_images]`

### How images are rendered on the product page

In the QWeb template `website_sale.shop_product_images` (`odoo/addons/website_sale/views/templates.xml`):

```xml
<t t-set="product_images" t-value="product_variant._get_images() if product_variant else product._get_images()"/>
```

This list is then iterated over in the carousel/grid templates (`shop_product_carousel`, `shop_product_grid`) to render each image.

### Ecommerce categories (`product.public.category`)

- Defined in `odoo/addons/website_sale/models/product_public_category.py`.
- Inherits `image.mixin` (has `image_1920` used as the category avatar/thumbnail).
- Has a `cover_image` field used only in the Category List Snippet.
- Linked to products via Many2many: `product.template.public_categ_ids` ↔ `product.public.category.product_tmpl_ids`.
- **Currently has NO concept of "extra images" that propagate to product carousels.**

### Current image flow (summary)

```
Product Page Carousel
  └── _get_images()
        ├── product.product main image (or fallback to template)
        ├── product.product variant extra images (product.image)
        └── product.template extra images (product.image)
```

Categories play **no role** in product image display.

---

## Proposed Changes

### Goal

Allow adding **extra images** on the Ecommerce Category form that are automatically appended to the product image carousel for every product in that category. A product in multiple categories gets images from all its categories.

### Image display order

```
Product Page Carousel (new)
  └── _get_images()
        ├── product.product main image (or fallback to template)
        ├── product.product variant extra images
        ├── product.template extra images
        └── category extra images (NEW — from all categories, ordered by category sequence)
```

Category images appear **after** all product-specific images, so product-level content always takes priority.

When a product belongs to a category that has parent categories, images from the **entire category hierarchy** are included — child categories first, then walking up to parents. For example, if a product is in "Chairs" (child of "Furniture"), the order is: Chairs images → Furniture images.

If a product belongs to multiple categories, each category's full hierarchy is included (ordered by category sequence), with deduplication to avoid repeating images from shared ancestors.

### Existing category images (`image_1920`, `cover_image`)

These are **not affected** by this module:

- **`image_1920`** (from `image.mixin`) — the category avatar/thumbnail used in the backend form and mega menu snippets. Stays as-is.
- **`cover_image`** — used only in the Category List Snippet on the frontend. Stays as-is.

Neither of these appears in product carousels. This module introduces a **new** set of extra images specifically for the carousel.

### Implementation plan

#### 1. New model: `product.public.category.image`

A new model to store extra images for a category, similar to `product.image`:

- `name` — `Char`, required
- `sequence` — `Integer`, for ordering
- `image_1920` — `Image` (inherits `image.mixin`)
- `category_id` — `Many2one` → `product.public.category`
- `can_image_1024_be_zoomed` — `Boolean`, computed (same logic as `product.image`)

#### 2. Extend `product.public.category`

Add a One2many field:

- `category_image_ids` — One2many → `product.public.category.image`

#### 3. Extend `_get_images()` on `product.template` and `product.product`

Override `_get_images()` to append category images (including hierarchy) after the existing images:

```python
# product.template
def _get_images(self):
    images = super()._get_images()
    seen_categories = set()
    for category in self.public_categ_ids.sorted('sequence'):
        # Walk up the hierarchy: child first, then parents
        for cat in category.parents_and_self.sorted(lambda c: -len(c.parent_path or '')):
            if cat.id not in seen_categories:
                seen_categories.add(cat.id)
                images += list(cat.category_image_ids)
    return images
```

```python
# product.product
def _get_images(self):
    images = super()._get_images()
    seen_categories = set()
    for category in self.product_tmpl_id.public_categ_ids.sorted('sequence'):
        for cat in category.parents_and_self.sorted(lambda c: -len(c.parent_path or '')):
            if cat.id not in seen_categories:
                seen_categories.add(cat.id)
                images += list(cat.category_image_ids)
    return images
```

#### 4. Extend the category form view

Add a notebook/tab on the `product.public.category` form to manage extra images (similar to how `product.template` manages `product_template_image_ids`):

```xml
<xpath expr="//sheet" position="inside">
    <notebook>
        <page string="Extra Images" name="extra_images">
            <field name="category_image_ids" mode="kanban" .../>
        </page>
    </notebook>
</xpath>
```

#### 5. No template changes required

The QWeb templates already iterate over whatever `_get_images()` returns. Since our new `product.public.category.image` model will inherit `image.mixin` (providing `image_1920`, `image_1024`, `image_128`, `can_image_1024_be_zoomed`), the existing carousel and grid templates will render category images without modification.

### Edge cases to handle

- **Shared ancestors**: If a product belongs to multiple categories that share a parent, `seen_categories` deduplication ensures parent images only appear once.
- **Performance**: Walking the hierarchy uses the pre-computed `parents_and_self` / `parent_path` fields, so no recursive queries are needed.

### Files to create/modify

| File                                      | Action                                              |
| ----------------------------------------- | --------------------------------------------------- |
| `models/__init__.py`                      | Create — import new models                          |
| `models/product_public_category.py`       | Create — extend category with `category_image_ids`  |
| `models/product_public_category_image.py` | Create — new `product.public.category.image` model  |
| `models/product_template.py`              | Create — override `_get_images()`                   |
| `models/product_product.py`               | Create — override `_get_images()`                   |
| `views/product_public_category_views.xml` | Create — extend category form with image management |
| `security/ir.model.access.csv`            | Create — access rights for new model                |
| `__manifest__.py`                         | Update — add data files                             |

---

## Testing Checklist

### Backend — Category Form

- [x] "eCommerce Media" section visible at the bottom of the category form
- [x] Can upload an image via "Add Media"
- [x] Image preview (thumbnail) shows in the kanban after saving
- [x] Image name is displayed below the thumbnail
- [ ] File size badge shows (green/yellow/red)
- [x] Can reorder images via drag handle
- [x] Can edit an image (click opens form dialog with name + image)
- [x] Can delete an image

### Frontend — Single Category

- [x] Product with one category: category images appear after product images in the carousel
- [x] Category images show in the correct sequence order
- [x] Image zoom works on category images (if large enough)
- [x] Carousel indicators/thumbnails include category images

### Frontend — Multiple Categories

- [x] Product in two categories: images from both categories appear
- [ ] Categories are ordered by their sequence field
- [ ] No duplicate images when categories share a parent

### Frontend — Category Hierarchy

- [x] Product in child category "Chairs" (parent "Furniture"): Chairs images appear first, then Furniture images
- [ ] Product in two sibling categories under the same parent: parent images appear only once

### Frontend — Edge Cases

- [ ] Product with no categories: carousel unchanged (only product images)
- [ ] Category with no extra images: no effect on carousel
- [ ] Product variant: category images appear after variant + template images
- [x] Grid layout: category images render correctly (not just carousel)

### Existing Functionality — No Regressions

- [x] Category avatar (`image_1920`) still shows in backend form and mega menu snippets
- [ ] Category cover image still works in the Category List Snippet
- [x] Product extra images still work as before
