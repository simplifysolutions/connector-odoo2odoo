# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

{
    'name': 'Odoo Connector - Attachment',
    'summary': '''Technical base for attachment related Odoo Connector
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
        'document',
        'odooconnector_base',
        'odooconnector_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ir_attachment_view.xml',
        'views/odooconnector_backend.xml',
    ],
    'demo': [
    ],
}
