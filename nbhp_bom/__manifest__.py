# -*- coding: utf-8 -*-
{
    'name': "MRP Bom Extension Module",

    'summary': """
        extend the mrp module for bom new feature(s).""",

    'description': """
        this module is designed to bom new features for mrp
    """,

    'author': "Olalekan Babawale",
    'website': "http://obabawale.github.io",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'mrp',
        'product',
        'nbhp_base'
    ],

    'data': [
        'data/sequence.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
    ],
}
