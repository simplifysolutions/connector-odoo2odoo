# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping, ExportMapper)
from ..unit.backend_adapter import OdooAdapter
from ..unit.import_synchronizer import (OdooImporter,
                                        DirectBatchImporter)
from ..unit.export_synchronizer import (OdooExporter,
                                        DirectBatchExporter)
from ..unit.mapper import OdooImportMapper
from ..backend import oc_odoo


_logger = logging.getLogger(__name__)


class OdooConnectorCrmLead(models.Model):
    _name = 'odooconnector.crm.lead'
    _inherit = 'odooconnector.binding'
    _inherits = {'crm.lead': 'openerp_id'}
    _description = 'Odoo Connector Crm Lead'

    openerp_id = fields.Many2one(
        comodel_name='crm.lead',
        string='Crm Lead',
        required=True,
        ondelete='restrict',
    )


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.crm.lead',
        inverse_name='openerp_id',
        string='Odoo Connector Binding'
    )


@oc_odoo
class CrmLeadBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.crm.lead']


@oc_odoo
class CrmLeadImporter(OdooImporter):
    _model_name = ['odooconnector.crm.lead']

    def _import_dependencies(self):
        record = self.external_record

        if record.get('partner_id'):
            binder = self.binder_for('odooconnector.res.partner')
            partner_id = binder.to_openerp(
                record['partner_id'][0], unwrap=True)
            if not partner_id:
                self._import_dependency(record['partner_id'][0],
                                        'odooconnector.res.partner')

@oc_odoo
class CrmLeadImportMapper(OdooImportMapper):
    _model_name = 'odooconnector.crm.lead'

    direct = [('name', 'name'), ('partner_name', 'partner_name'),
              ('contact_name', 'contact_name'), ('street', 'street'),
              ('street2', 'street2'), ('city', 'city'),
              ('zip', 'zip'), ('phone', 'phone'),
              ('mobile', 'mobile'), ('fax', 'fax'), ('email_from', 'email_from'),
              ('probability', 'probability'), ('planned_revenue', 'planned_revenue'),
              ('date_deadline', 'date_deadline'), ('date_action', 'date_action'),
              ('title_action', 'title_action'), ('opt_out', 'opt_out'),
              ('referred', 'referred'), ('description', 'description'),
              ('priority', 'priority'),
              ]

    @mapping
    def priority(self, record):
        if not record.get('priority'):
            return
        priority = (int(record.get('priority'))==3) and str(int(record.get('priority'))+1) or record.get('priority')
        return {'priority': priority}

    @mapping
    def stage_id(self,record):
        if not record.get('stage_id'):
            return
        crm_stage=self.env['crm.case.stage']
        stage=crm_stage.search([('name','=',record.get('stage_id')[1])])
        if not stage:
            adapter = self.unit_for(OdooAdapter)
            stage_data=adapter.read(record.get('stage_id')[0],model_name='crm.stage')[0]
            stage=crm_stage.create(stage_data)
        return {'stage_id':stage.id}

    @mapping
    def partner_id(self, record):
        if not record.get('partner_id'):
             return
        binder = self.binder_for('odooconnector.res.partner')
        partner_id = binder.to_openerp(record['partner_id'][0], unwrap=True)
        return {'partner_id': partner_id}

@oc_odoo
class CrmLeadExporter(OdooExporter):
    _model_name = ['odooconnector.crm.lead']

    def _get_remote_model(self):
        return 'crm.lead'

    def _pre_export_check(self, record):
        if not self.backend_record.default_export_lead:
            return False

        domain = self.backend_record.default_export_lead_domain
        return self._pre_export_domain_check(record, domain)

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
                model_name='odooconnector.crm.lead',
                context={'connector_no_export': True}
            )


@oc_odoo
class CrmLeadExportMapper(ExportMapper):
    _model_name = 'odooconnector.crm.lead'

    direct = [('name', 'name'), ('partner_name', 'partner_name'),
              ('contact_name', 'contact_name'), ('street', 'street'),
              ('street2', 'street2'), ('city', 'city'),
              ('zip', 'zip'), ('phone', 'phone'),
              ('mobile', 'mobile'), ('fax', 'fax'), ('email_from', 'email_from'),
              ('probability', 'probability'), ('planned_revenue', 'planned_revenue'),
              ('date_deadline', 'date_deadline'), ('date_action', 'date_action'),
              ('title_action', 'title_action'), ('opt_out', 'opt_out'),
              ('referred', 'referred'), ('description', 'description'),
              ]

    @mapping
    def priority(self, record):
        if not record.priority:
            return
        priority = (int(record.priority)==4) and str(int(record.priority)-1) or record.priority
        return {'priority': priority}

    @mapping
    def stage_id(self,record):
        stage=record.stage_id
        adapter = self.unit_for(OdooAdapter)
        stage_id = adapter.search([('name','=',stage.name)],
            model_name='crm.stage')
        if not stage_id:
            vals={'name':stage.name,
            'on_change':stage.on_change,
            'fold':stage.fold,
            'probability':stage.probability,
            }
            stage_id = adapter.create(vals,model_name='crm.stage')
        if isinstance(stage_id,list):
            stage_id=stage_id[0]
        return {'stage_id': stage_id}

    @mapping
    def partner_id(self, record):
        if not record.partner_id:
            return
        binder = self.binder_for('odooconnector.res.partner')
        partner_id = binder.to_backend(record.partner_id.id, wrap=True)
        return {'partner_id': partner_id}

    # TODO: After users synch, add salesperson mapping

