# -*- coding: utf-8 -*-
{
    'name': "Material Requisition",

    'summary': """
        Material requisition module...""",

    'description': """
        Material requisition module...
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Stock',
    'version': '0.1',

    'depends': ['base', 'hr', 'product', 'stock','purchase'],


    'data': [
        'security/store_requisition_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/interstore.xml',
        'views/company.xml',
        'data/mail_template.xml',
        'data/sequence.xml',
        'wizards/ir_request.xml',
    ],
}