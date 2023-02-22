# -*- coding: utf-8 -*-
{
    'name': "NBHP Sales Ext Module",

    'summary': """
        NBHP Sales Ext Module.""",

    'description': """
        this module is designed to extend the Sales module 
    """,

    'author': "Olalekan Babawale",
    'website': "http://obabawale.github.io",
    'license': 'LGPL-3',

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': [
        'base',
        'nbhp_base',
        'sale_management',
    ],

    'data': [
        'views/sale_order_view.xml',
    ],
}
