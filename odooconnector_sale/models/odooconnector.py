# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime
from openerp import models, fields,api
from openerp.tools.safe_eval import safe_eval

from openerp.addons.connector.session import ConnectorSession
from openerp.addons.odooconnector_base.unit.import_synchronizer import import_batch


class OdooBackend(models.Model):

    _inherit = 'odooconnector.backend'


    default_export_sale_order = fields.Boolean(
        string='Default SO export backend',
        help='Use this backend as default for the SO process.'
    )
    default_export_so_domain = fields.Char(
        string='Export Sale Order Domain',
        default='[]'
    )
    default_import_so_domain = fields.Char(
        string='Import Sale Order Domain',
        default='[]'
    )
    import_so_since=fields.Datetime(
        string='Import SO Since'
    )

    @api.model
    def import_sale_order(self):
        """ Import sale order from external system """
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        backends=self.search([('version','=','1000')])
        for backend in backends:
            filters = backend.default_import_so_domain
            if filters and isinstance(filters, (str,unicode)):
                filters = safe_eval(filters)
            domain=[('write_date','>=',backend.import_so_since)]
            import_batch(session, 'odooconnector.sale.order', backend.id,
                         filters+domain)
            backend.write({'import_so_since':datetime.datetime.now()})

        return True
    
    @api.multi
    def export_so(self):
        """ Export sale orders to external system """
        self._export_records('sale.order')
        return True
