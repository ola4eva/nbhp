{
    'name': "Account Extension",
    'summary': """
        Account Extension
    """,
    'description': """
        Account Extension
    """,
    'category': 'Account',
    'depends': ['account', 'account_reports'],
    'data': [
        'data/data_analytic_account.xml',
        # 'views/account_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
