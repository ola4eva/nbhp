# -*- coding: utf-8 -*-
{
    'name': "NBHP Vendor Registration",

    'summary': """
    NBHP vendor registration
    """,

    'description': """
        Vendor Registration
    """,

    'author': "Olalekan Babawale",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base'],

    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_request_views.xml',
    ],
    'license': 'LGPL-3',
}
