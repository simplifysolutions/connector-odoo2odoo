# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

from openerp import models, fields
from openerp.addons.connector.unit.mapper import (
    ExportMapper, ImportMapper, mapping)
from openerp.addons.odooconnector_base.unit.backend_adapter import OdooAdapter
from openerp.addons.odooconnector_base.backend import oc_odoo
from openerp.addons.odooconnector_base.unit.import_synchronizer import (
    OdooImporter, DirectBatchImporter)
from openerp.addons.odooconnector_base.unit.mapper import OdooImportMapper
from openerp.addons.odooconnector_base.unit.export_synchronizer import (
    OdooExporter)


class OdooConnectorAttachment(models.Model):
    _name = 'odooconnector.ir.attachment'
    _inherit = 'odooconnector.binding'
    _inherits = {'ir.attachment': 'openerp_id'}
    _description = 'Odoo Connector Attachment'

    openerp_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment',
        required=True,
        ondelete='restrict'
    )


class Attachements(models.Model):
    _inherit = 'ir.attachment'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.ir.attachment',
        inverse_name='openerp_id',
        string='Odoo Binding'
    )


@oc_odoo
class AttachmentsBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.ir.attachment']


@oc_odoo
class AttachmentsImporter(OdooImporter):
    _model_name = ['odooconnector.ir.attachment']


@oc_odoo
class AttachmentsImporterMapper(OdooImportMapper):
    _model_name = ['odooconnector.ir.attachment']

    direct = [
        ('name', 'name'),
        ('type', 'type'),
        ('datas', 'datas'),
        ('datas_fname', 'datas_fname'),
        ('res_model', 'res_model'),
        ('res_id', 'res_id'),
        ('res_name', 'res_name'),
        ('description', 'description'),
        ('create_date', 'create_date'),
        ('file_type', 'mimetype'),
    ]


@oc_odoo
class AttachmentsExporter(OdooExporter):
    _model_name = ['odooconnector.ir.attachment']

    def _get_remote_model(self):
        return 'ir.attachment'

    def _pre_export_check(self, record):
        if not self.backend_record.default_export_ir_attachment:
            return False
        domain = self.backend_record.default_export_ir_attachment_domain
        return self._pre_export_domain_check(record, domain)

    def _after_export(self, record_created):
        # create a ic_binding in the backend, indicating that the attachment
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
                model_name='odooconnector.ir.attachment',
                context={'connector_no_export': True}
            )


@oc_odoo
class AttachmentsExporterMapper(ExportMapper):
    _model_name = ['odooconnector.ir.attachment']

    direct = [
        ('name', 'name'),
        ('type', 'type'),
        ('datas', 'datas'),
        ('datas_fname', 'datas_fname'),
        ('res_model', 'res_model'),
        ('res_id', 'res_id'),
        ('res_name', 'res_name'),
        ('description', 'description'),
        ('create_date', 'create_date'),
        ('file_type', 'mimetype'),
    ]

    @mapping
    def create_uid(self, record):
        if record.create_uid:
            binder = self.binder_for('odooconnector.res.users')
            uid = binder.to_backend(record.create_uid.id, wrap=True)
            if uid:
                return {'create_uid': uid}

    @mapping
    def sales_team(self, record):
        if record.sales_team_id:
            binder = self.binder_for('odooconnector.crm.case.section')
            sales_team_id = binder.to_backend(
                record.sales_team_id.id, wrap=True)
            if sales_team_id:
                return {'sales_team_id': sales_team_id}

    @mapping
    def sales_person(self, record):
        if record.sales_person:
            binder = self.binder_for('odooconnector.res.users')
            sales_person_id = binder.to_backend(record.sales_person.id, wrap=True)
            if sales_person_id:
                return {'sales_person': sales_person_id}
