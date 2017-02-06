# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

{
    'name': 'Odoo Connector - CRM',
    'summary': '''Technical base for CRM related Odoo Connector
                scenarios''',
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
        'crm',
        'odooconnector_base',
        'odooconnector_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead.xml',
        'views/odooconnector_backend.xml',
        'views/scheduler.xml',
    ],
    'demo': [
    ],
}
