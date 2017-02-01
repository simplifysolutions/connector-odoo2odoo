# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

import datetime
from openerp import models, fields, api
from openerp.tools.safe_eval import safe_eval

from openerp.addons.connector.session import ConnectorSession
from openerp.addons.odooconnector_base.unit.import_synchronizer import import_batch


class OdooBackend(models.Model):

    _inherit = 'odooconnector.backend'

    default_export_sales_team = fields.Boolean(
        string='Default Sales Team export backend',
        help='Use this backend as default for the SO process.'
    )
    default_export_sales_team_domain = fields.Char(
        string='Export Sales Team Domain',
        default='[]'
    )
    default_export_sale_order = fields.Boolean(
        string='Default SO export backend',
        help='Use this backend as default for the SO process.'
    )
    default_export_so_domain = fields.Char(
        string='Export Sale Order Domain',
        default='[]'
    )
    default_export_account_tax = fields.Boolean(
        string='Default Account Tax export backend',
        help='Use this backend as default for the SO process.'
    )
    default_export_account_tax_domain = fields.Char(
        string='Export Account Tax Domain',
        default='[]'
    )
    default_import_so_domain = fields.Char(
        string='Import Sale Order Domain',
        default='[]'
    )
    import_so_since = fields.Datetime(
        string='Import SO Since'
    )

    @api.model
    def import_sale_order(self):
        """ Import sale order from external system """
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        backends = self.search([('version', '=', '1000')])
        for backend in backends:
            filters = backend.default_import_so_domain
            if filters and isinstance(filters, (str, unicode)):
                filters = safe_eval(filters)
            domain = [('write_date', '>=', backend.import_so_since)]
            import_batch(session, 'odooconnector.sale.order', backend.id,
                         filters + domain)
            backend.write({'import_so_since': datetime.datetime.now()})

        return True

    @api.multi
    def import_so(self):
        return self.import_sale_order()

    @api.multi
    def export_sales_team(self):
        """ Export sale orders to external system """
        self._export_records('crm.case.section')
        return True

    @api.multi
    def export_so(self):
        """ Export sale orders to external system """
        self._export_records('sale.order')
        return True

    @api.multi
    def export_so_line(self):
        """ Export sale orders to external system """
        self._export_records('sale.order.line')
        return True

    @api.multi
    def export_taxes(self):
        """ Export sale orders to external system """
        self._export_records('account.tax')
        return True
