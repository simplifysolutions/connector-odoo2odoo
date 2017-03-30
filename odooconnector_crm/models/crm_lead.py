# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping, ExportMapper)
from openerp.addons.odooconnector_base.unit.backend_adapter import OdooAdapter
from openerp.addons.odooconnector_base.unit.import_synchronizer import (
    OdooImporter, DirectBatchImporter)
from openerp.addons.odooconnector_base.unit.export_synchronizer import (
    OdooExporter, DirectBatchExporter)
from openerp.addons.odooconnector_base.unit.mapper import OdooImportMapper
from openerp.addons.odooconnector_base.backend import oc_odoo


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

    direct = [('name', 'name'),
              ('partner_name', 'partner_name'),
              ('contact_name', 'contact_name'),
              ('street', 'street'),
              ('street2', 'street2'),
              ('city', 'city'),
              ('zip', 'zip'),
              ('phone', 'phone'),
              ('mobile', 'mobile'),
              ('fax', 'fax'),
              ('email_from', 'email_from'),
              ('probability', 'probability'),
              ('planned_revenue', 'planned_revenue'),
              ('date_deadline', 'date_deadline'),
              ('date_action', 'date_action'),
              ('title_action', 'title_action'),
              ('opt_out', 'opt_out'),
              ('referred', 'referred'),
              ('description', 'description'),
              ('active', 'active'),
              ('store_no', 'store_no'),
              ]

    @mapping
    def priority(self, record):
        if not record.get('priority'):
            return
        priority = (int(record.get('priority')) == 3) and str(
            int(record.get('priority')) + 1) or record.get('priority')
        return {'priority': priority}

    @mapping
    def stage_id(self, record):
        if not record.get('stage_id'):
            return
        crm_stage = self.env['crm.case.stage']
        stage = crm_stage.search([('name', '=', record.get('stage_id')[1])])
        if not stage:
            adapter = self.unit_for(OdooAdapter)
            stage_data = adapter.read(
                record.get('stage_id')[0],
                model_name='crm.stage')[0]
            stage = crm_stage.create(stage_data)
        return {'stage_id': stage.id}

    @mapping
    def partner_id(self, record):
        if not record.get('partner_id'):
            return
        binder = self.binder_for('odooconnector.res.partner')
        partner_id = binder.to_openerp(record['partner_id'][0], unwrap=True)
        return {'partner_id': partner_id}

    @mapping
    def user_id(self, record):
        if not record.get('user_id'):
            return
        binder = self.binder_for('odooconnector.res.users')
        user_id = binder.to_openerp(record['user_id'][0], unwrap=True)
        return {'user_id': user_id}

    @mapping
    def section_id(self, record):
        if not record.get('team_id'):
            return
        binder = self.binder_for('odooconnector.crm.case.section')
        section_id = binder.to_openerp(record['team_id'][0], unwrap=True)
        if section_id:
            return {'section_id': section_id}

    @mapping
    def tag_ids(self, record):
        if not record.get('tag_ids'):
            return
        tag_ids = []
        adapter = self.unit_for(OdooAdapter)
        tags = adapter.read(record.get('tag_ids'), model_name='crm.lead.tag')
        crm_tags = self.env['crm.case.categ']
        for each_tag in tags:
            tag = crm_tags.search([('name', '=', each_tag['name'])])
            if not tag:
                tag = crm_tags.create({'name': each_tag['name']})
            if isinstance(tag, list):
                tag = tag[0]
            tag_ids.append(tag.id)
        return {'categ_ids': [(6, 0, tag_ids)]}


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

    direct = [('name', 'name'),
              ('partner_name', 'partner_name'),
              ('contact_name', 'contact_name'),
              ('street', 'street'),
              ('street2', 'street2'),
              ('city', 'city'),
              ('zip', 'zip'),
              ('phone', 'phone'),
              ('mobile', 'mobile'),
              ('fax', 'fax'),
              ('email_from', 'email_from'),
              ('probability', 'probability'),
              ('planned_revenue', 'planned_revenue'),
              ('date_deadline', 'date_deadline'),
              ('date_action', 'date_action'),
              ('title_action', 'title_action'),
              ('opt_out', 'opt_out'),
              ('referred', 'referred'),
              ('description', 'description'),
              ('active', 'active'),
              ('store_no', 'store_no'),
              ]

    @mapping
    def priority(self, record):
        if not record.priority:
            return
        priority = (int(record.priority) == 4) and str(
            int(record.priority) - 1) or record.priority
        return {'priority': priority}

    @mapping
    def stage_id(self, record):
        stage = record.stage_id
        adapter = self.unit_for(OdooAdapter)
        stage_id = adapter.search([('name', '=', stage.name)],
                                  model_name='crm.stage')
        if not stage_id:
            vals = {'name': stage.name,
                    'on_change': stage.on_change,
                    'fold': stage.fold,
                    'probability': stage.probability,
                    }
            stage_id = adapter.create(vals, model_name='crm.stage')
        if isinstance(stage_id, list):
            stage_id = stage_id[0]
        return {'stage_id': stage_id}

    @mapping
    def partner_id(self, record):
        if not record.partner_id:
            return
        binder = self.binder_for('odooconnector.res.partner')
        partner_id = binder.to_backend(record.partner_id.id, wrap=True)
        return {'partner_id': partner_id}

    @mapping
    def user_id(self, record):
        if not record.user_id:
            return
        binder = self.binder_for('odooconnector.res.users')
        user_id = binder.to_backend(record.user_id.id, wrap=True)
        if user_id:
            return {'user_id': user_id}

    # section_id is team_id  in v10
    @mapping
    def team_id(self, record):
        binder = self.binder_for('odooconnector.crm.case.section')
        team_id = binder.to_backend(record.section_id.id, wrap=True)
        if team_id:
            return {'team_id': team_id}

    @mapping
    def tag_ids(self, record):
        if not record.categ_ids:
            return
        tag_ids = []
        for each_tag in record.categ_ids:
            adapter = self.unit_for(OdooAdapter)
            tag_id = adapter.search([('name', '=', each_tag.name)],
                                    model_name='crm.lead.tag')
            if not tag_id:
                tag_id = adapter.create({'name': each_tag.name},
                                        model_name='crm.lead.tag')
            if isinstance(tag_id, list):
                tag_id = tag_id[0]
            tag_ids.append(tag_id)
        return {'tag_ids': [(6, 0, tag_ids)]}
