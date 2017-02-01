# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

from openerp import models, fields, api
from openerp.addons.connector.unit.mapper import (
    ExportMapper, ImportMapper, mapping)
from openerp.addons.odooconnector_base.unit.backend_adapter import OdooAdapter
from openerp.addons.odooconnector_base.backend import oc_odoo
from openerp.addons.odooconnector_base.unit.import_synchronizer import (
    OdooImporter, DirectBatchImporter)
from openerp.addons.odooconnector_base.unit.mapper import OdooImportMapper
from openerp.addons.odooconnector_base.unit.export_synchronizer import (
    OdooExporter)


class OdooConnectorResUsers(models.Model):
    _name = 'odooconnector.res.users'
    _inherit = 'odooconnector.binding'
    _inherits = {'res.users': 'openerp_id'}
    _description = 'Odoo Connector Users'

    openerp_id = fields.Many2one(
        comodel_name='res.users',
        string='Users',
        required=True,
        ondelete='restrict'
    )


class ResUsers(models.Model):
    _inherit = 'res.users'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.res.users',
        inverse_name='openerp_id',
        string='Odoo Binding'
    )


@oc_odoo
class ResUsersBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.res.users']


@oc_odoo
class ResUsersImporter(OdooImporter):
    _model_name = ['odooconnector.res.users']


@oc_odoo
class ResUsersImporterMapper(OdooImportMapper):
    _model_name = ['odooconnector.res.users']

    direct = [
        ('name', 'name'), ('login', 'login'),
        ('password', 'password'), ('password_crypt', 'password_crypt'),
        ('signature', 'signature'), ('notify_email', 'notify_email'),
    ]


@oc_odoo
class ResUsersExporter(OdooExporter):
    _model_name = ['odooconnector.res.users']

    def _get_remote_model(self):
        return 'res.users'

    def _pre_export_check(self, record):
        if not record.external_id:
            adapter = self.unit_for(OdooAdapter)
            user_id = adapter.search([('name', '=', record.openerp_id.name),
                                      ('login', '=', record.openerp_id.login)],
                                     model_name='res.users')
#            if user_id:
#                record.write({'external_id':user_id[0]})
        if not self.backend_record.default_export_res_users:
            return False
        domain = self.backend_record.default_export_res_users_domain
        return self._pre_export_domain_check(record, domain)

    def _after_export(self, record_created):
        # create a ic_binding in the backend, indicating that the user
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
                model_name='odooconnector.res.users',
                context={'connector_no_export': True}
            )


@oc_odoo
class ResUsersExporterMapper(ExportMapper):
    _model_name = ['odooconnector.res.users']

    direct = [
        ('name', 'name'), ('login', 'login'),
        #        ('password','password'),
        ('password_crypt', 'password_crypt'),
        ('signature', 'signature'), ('notify_email', 'notify_email'),
        ('active', 'active')
    ]

    @mapping
    def action_id(self, record):
        if not record.action_id:
            return
        adapter = self.unit_for(OdooAdapter)
        action_id = adapter.search([('name', '=', record.action_id.name)],
                                   model_name='ir.actions.actions')
        if action_id:
            return {'action_id': action_id[0]}

    @mapping
    def partner_id(self, record):
        if not record.partner_id:
            return
        binder = self.binder_for('odooconnector.res.partner')
        partner_id = binder.to_backend(record.partner_id.id, wrap=True)
        return {'partner_id': partner_id}
