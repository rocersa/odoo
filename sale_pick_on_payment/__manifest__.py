# -*- coding: utf-8 -*-
{
    "name": "Sale Pick On Payment",
    "version": "19.0.1.0.0",
    "summary": "Create the delivery when the invoice is paid, not at confirmation",
    "description": """
Sale pick on payment
====================

The delivery is created when the order is paid, not when it is confirmed.

Why
---

Confirming a sale order used to launch the delivery route in the same instant,
so the yard packed and dispatched before any money arrived. On 2026-11-25,
confirming S00303 produced posted invoice INV/26-27/0058 with payment state
*Not Paid* and pick AUC/PICK/00106 together, with no payment recorded on the
order. This module is the creation gate, not the validation or print gate: the
pick does not exist until the order is paid for or deliberately released.

What it does
------------

- Suppresses the stock-rule launch for a confirmed order until it is released.
  ``sale.order.line._action_launch_stock_rule`` only runs for an order whose
  delivery is released, so confirmation, later line edits and any other path
  cannot create a pick early.
- Releases the order when all of its posted customer invoices are fully
  settled (``paid`` or ``in_payment``). A partial payment does not release it.
- Creates the delivery exactly once, and only when no active delivery exists.
  A second payment or a re-save does not create a second pick.
- Never silently recreates a pick that was cancelled: an automatic release
  stops if any pick already exists, including a cancelled one.
- Adds **Create Delivery** on the sale order for an urgent order or a trusted
  customer. A manual release records who released it and when (on the order and
  in the chatter), so a release can be seen after the fact. Pressing it again
  reuses the existing delivery.

Decisions (Harry, 2026-11-26)
-----------------------------

- **Full payment only.** A partially paid invoice does not release the pick.
  A payment that is registered but not yet bank-matched (``in_payment``) counts
  as full payment.
- **No account-customer exemption.** No partner carries payment terms and the
  only term in use is *Internet bank transfer prior to dispatch*, so there is no
  on-account path to accommodate. Every order waits for payment or a manual
  release.
- **A cancelled pick is not recreated automatically.** Staff can still create a
  fresh delivery explicitly with **Create Delivery**.

Dependency
----------

Odoo currently receives no payments: every posted AU invoice since 2026-09-26
is unpaid and the CommBank feed stops at 2026-05-19 (``commbank-bank-sync``,
parked on Harry). Until a payment signal exists, the automatic release never
fires and every order waits for the manual action. Do not deploy this ahead of a
working payment feed without accepting that.

The carrier guard (``block-sale-order-confirmation-without-a-shipping-method``)
is complementary: the carrier is set at confirmation, and the delivery created
later reads it from the order, so the pick still prints the shipping method.
""",
    "author": "Rocersa",
    "category": "Rocersa/Sales",
    "license": "AGPL-3",
    "depends": ["sale_stock"],
    "data": [
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
