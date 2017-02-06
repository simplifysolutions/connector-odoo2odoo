# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

from openerp import models, fields
from openerp.tools.safe_eval import safe_eval
from openerp.addons.connector.unit.mapper import (
    ExportMapper, ImportMapper, mapping)
from openerp.addons.odooconnector_base.unit.backend_adapter import OdooAdapter
from openerp.addons.odooconnector_base.backend import oc_odoo
from openerp.addons.odooconnector_base.unit.import_synchronizer import (
    OdooImporter, DirectBatchImporter)
from openerp.addons.odooconnector_base.unit.mapper import OdooImportMapper
from openerp.addons.odooconnector_base.unit.export_synchronizer import (
    OdooExporter)


class OdooConnectorCrmCaseSection(models.Model):
    _name = 'odooconnector.crm.case.section'
    _inherit = 'odooconnector.binding'
    _inherits = {'crm.case.section': 'openerp_id'}
    _description = 'Odoo Connector Sales Team'

    openerp_id = fields.Many2one(
        comodel_name='crm.case.section',
        string='Sales Team',
        required=True,
        ondelete='restrict'
    )


class CrmCaseSection(models.Model):
    _inherit = 'crm.case.section'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.crm.case.section',
        inverse_name='openerp_id',
        string='Odoo Binding'
    )


@oc_odoo
class CrmCaseSectionBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.crm.case.section']


@oc_odoo
class CrmCaseSectionImporter(OdooImporter):
    _model_name = ['odooconnector.crm.case.section']


@oc_odoo
class CrmCaseSectionImporterMapper(OdooImportMapper):
    _model_name = ['odooconnector.crm.case.section']

    direct = [
        ('name', 'name'), ('use_quotations', 'use_quotations'),
        ('use_leads', 'use_leads'), ('use_opportunities', 'use_opportunities'),
        ('invoiced_target', 'invoiced_target'),('alias_name','alias_name'),
        ('alias_contact','alias_contact'),('color','color')
    ]


@oc_odoo
class CrmCaseSectionExporter(OdooExporter):
    _model_name = ['odooconnector.crm.case.section']

    def _get_remote_model(self):
        return 'crm.team'

    def _pre_export_check(self, record):
        if not record.external_id:
            adapter = self.unit_for(OdooAdapter)
            team_id = adapter.search([('name', '=', record.name)],
                                     model_name='crm.team')
            if team_id:
                record.write({'external_id': team_id[0]})
        if not self.backend_record.default_export_sales_team:
            return False
        domain = self.backend_record.default_export_sales_team_domain
        results = self.env['crm.case.section'].search(
            safe_eval(domain))
        if record.openerp_id.id in results.ids:
            return True
        return False
#        return self._pre_export_domain_check(record, domain)

    def _after_export(self, record_created):
        # create a ic_binding in the backend, indicating that the partner
        # was exported
        if record_created:
            record_id = self.binder.unwrap_binding(self.binding_id)
            data = {
                'backend_id': self.backend_record.export_backend_id,
                'openerp_id': self.external_id,
                'external_id': record_id,
                'exported_record': False
            }
            self.backend_adapter.create(
                data,
                model_name='odooconnector.crm.case.section',
                context={'connector_no_export': True}
            )


@oc_odoo
class CrmCaseSectionExporterMapper(ExportMapper):
    _model_name = ['odooconnector.crm.case.section']

    direct = [
        ('name', 'name'), ('use_quotations', 'use_quotations'),
        ('use_leads', 'use_leads'), ('use_opportunities', 'use_opportunities'),
        ('invoiced_target', 'invoiced_target'),('alias_name','alias_name'),
        ('alias_contact','alias_contact'),('color','color')
    ]

    @mapping
    def member_ids(self, record):
        if not record.member_ids:
            return
        member_ids = []
        binder = self.binder_for('odooconnector.res.users')
        for each_member in record.member_ids:
            user_id = binder.to_backend(each_member.id, wrap=True)
            if user_id:
                member_ids.append(user_id)
        # member_ids is one2many in v10
        return {'member_ids': [(6, False, member_ids)]}

    @mapping
    def user_id(self, record):
        if not record.user_id:
            return
        binder = self.binder_for('odooconnector.res.users')
        user_id = binder.to_backend(record.user_id.id, wrap=True)
        if user_id:
            return {'user_id': user_id}
