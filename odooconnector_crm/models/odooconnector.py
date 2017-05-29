# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

import datetime
from openerp import models, fields, api
from openerp.tools.safe_eval import safe_eval

from openerp.addons.connector.session import ConnectorSession
from openerp.addons.odooconnector_base.unit.import_synchronizer import import_batch

domain = {'domain': ['|', ('active', '=', True), ('active', '=', False)]}


class OdooBackend(models.Model):

    _inherit = 'odooconnector.backend'

    import_lead_domain_filter = fields.Char(
        string='Import CRM Lead Domain',
        default='[]'
    )

    import_leads_since = fields.Datetime(
        string='Import CRM Leads Since',
        default=datetime.datetime.now()

    )

    default_export_lead = fields.Boolean(
        string='Export Crm Leads'
    )

    default_export_lead_domain = fields.Char(
        string='Export Crm Leads Domain',
        default='[]'
    )

    @api.model
    def import_crm_leads(self):
        """ Import leads from external system """
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        backends = self.search([('version', '=', '1000')])
        for backend in backends:
            filters = backend.import_lead_domain_filter
            if filters and isinstance(filters, (str, unicode)):
                filters = safe_eval(filters)
            crm_domain = [('write_date', '>=', backend.import_leads_since)]
            import_batch(session, 'odooconnector.crm.lead', backend.id,
                         filters + crm_domain)
            backend.write({'import_leads_since': datetime.datetime.now()})

        return True

    @api.multi
    def import_leads(self):
        return self.import_crm_leads()

    @api.multi
    def export_leads(self):
        """ Export Leads to external system """
        self.with_context(domain)._export_records('crm.lead')
        return True
