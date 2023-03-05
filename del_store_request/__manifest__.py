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

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'product', 'stock','purchase'],


    # always loaded
    'data': [
        'security/store_requisition_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/interstore.xml',
        'views/company.xml',
        # 'views/templates.xml',
        'data/mail_template.xml',
        'data/sequence.xml',
        # 'views/hr_department.xml',
        # 'views/ir_request.xml',
        'wizards/ir_request.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}