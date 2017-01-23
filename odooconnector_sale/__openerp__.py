# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Odoo Connector - Sale',
    'summary': 'Technical base for sale related Odoo Connector scenarios',
    'version': '8.0.1.0.0',
    'category': 'Connector',
    'website': '',
    'author': 'Bista Solutions',
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'external_dependencies': {
    },
    'depends': [
        'base',
        'sale',
        'odooconnector_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_view.xml',
        'views/account_tax_view.xml',
        'views/odooconnector_backend.xml',
        'views/scheduler.xml',
    ],
    'demo': [
    ],
}
