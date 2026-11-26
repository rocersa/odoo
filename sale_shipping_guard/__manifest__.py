# -*- coding: utf-8 -*-
{
    "name": "Sale Shipping Guard",
    "version": "19.0.1.0.0",
    "summary": "Require a delivery method before confirming an order of physical goods",
    "description": """
Sale shipping guard
===================

Refuses to confirm a quotation that contains physical products until a delivery
method (``carrier_id``) is selected. The user sees:

    Please select a shipping method before confirming this order.

The guard hooks ``sale.order._confirmation_error_message``, which
``action_confirm`` calls before any state change, so a non-empty return blocks
the confirmation. It calls ``super()`` first, so core errors (wrong state, a
line with no product) take precedence.

What passes:

- An order with a carrier, including the *Collect* pickup carrier.
- A service-only order.
- A sections/notes-only order (vacuously all-service).

What is blocked:

- Any order with a non-service line and no carrier.

Quotations still save and send as draft. The guard does not touch the website
checkout: orders that reach payment post-processing are affected only when the
payment path confirms them, and our website orders arrive as drafts that the
back office confirms.

Requested 2026-11 (roadmap: block-sale-order-confirmation-without-a-shipping-
method) after picks printed without a Carrier or Shipping Method because
quotations had been confirmed with no delivery method.
""",
    "author": "Rocersa",
    "category": "Rocersa/Sales",
    "license": "AGPL-3",
    "depends": ["sale_management", "delivery"],
    "installable": True,
    "application": False,
}
