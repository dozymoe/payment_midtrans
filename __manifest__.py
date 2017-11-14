# -*- coding: utf-8 -*-

{
    'name': 'Midtrans Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: Midtrans',
    'version': '1.0',
    'description': """
        Unofficial module for Midtrans payment gateway.
    """,
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_midtrans_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,

    'author': 'Fahri Reza <dozymoe@gmail.com>',
    'website': 'http://dozy.moe',
}
