# -*- coding: utf-8 -*-
{
    'name': "Purchase Request Extension",

    'summary': """
        Purchase request extension.""",

    'description': """
        Purchase request extension.
    """,

    'author': "Olalekan Babawale",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/do_reject_views.xml',
    ],
}
