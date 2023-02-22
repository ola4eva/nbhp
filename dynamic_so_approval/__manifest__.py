# -*- coding: utf-8 -*-
{
    'name': "Dynamic Sale Approval",
    'category': 'Sale',
    'version': '15.1.0',
    'author': 'Olalekan Babawale',
    'description': """
        This module allows you to approve sale order users or group wise.
    """,
    'summary': """Sale Approval""",
    'depends': [
        'base',
        'sale_management',
        'sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/config_so_approval.xml',
        'views/sale_order_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
