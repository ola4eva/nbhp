# -*- coding: utf-8 -*-
{
    'name': "Scrap Workflow Ext Module",

    'summary': """
        Scrap Workflow  Module.""",

    'description': """
        this module is designed to handle the scrap workflow feature
    """,

    'author': "Olalekan Babawale",
    'website': "http://obabawale.github.io",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'hr',
        'stock',
        'account',
    ],

    'data': [
        'security/nbhp_groups.xml',
        'security/scrap_security.xml',
        'views/stock_scrap_views.xml',
    ],
}
