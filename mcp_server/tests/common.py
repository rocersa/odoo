# -*- coding: utf-8 -*-
"""Shared HTTP test base for the MCP suite.

Kept as a named subclass so the test files have one place to grow 20-specific
HTTP-test behaviour. It deliberately does not override ``url_open``: Odoo 20's
``HttpCase`` already routes test requests to the test cursor, and wrapping each
request in ``allow_requests`` re-acquires the registry test lock (harmless on
its own, noisy across the suite).
"""
from odoo.tests.common import HttpCase


class McpHttpCase(HttpCase):
    pass
