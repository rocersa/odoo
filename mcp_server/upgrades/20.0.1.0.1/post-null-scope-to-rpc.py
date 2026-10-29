# -*- coding: utf-8 -*-
"""Odoo 20 matches API-key scope exactly; migrate legacy NULL keys to ``rpc``."""


def migrate(cr, version):
    cr.execute("UPDATE res_users_apikeys SET scope = 'rpc' WHERE scope IS NULL")
