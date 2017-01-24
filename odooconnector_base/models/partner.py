# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping, ExportMapper)

from ..unit.import_synchronizer import (OdooImporter,
                                        DirectBatchImporter)
from ..unit.export_synchronizer import (OdooExporter,
                                        DirectBatchExporter)
from ..unit.backend_adapter import OdooAdapter

from ..unit.mapper import OdooImportMapper
from ..backend import oc_odoo


_logger = logging.getLogger(__name__)


class OdooConnectorPartner(models.Model):
    _name = 'odooconnector.res.partner'
    _inherit = 'odooconnector.binding'
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'Odoo Connector Partner'

    openerp_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='restrict',
    )


class ResPartner(models.Model):
    _inherit = 'res.partner'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.res.partner',
        inverse_name='openerp_id',
        string='Odoo Connector Binding'
    )


@oc_odoo
class PartnerBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.res.partner']


@oc_odoo
class PartnerImporter(OdooImporter):
    _model_name = ['odooconnector.res.partner']


@oc_odoo
class PartnerImportMapper(OdooImportMapper):
    _model_name = 'odooconnector.res.partner'

    direct = [('name', 'name'), ('is_company', 'is_company'),
              ('street', 'street'), ('street2', 'street2'), ('city', 'city'),
              ('zip', 'zip'), ('website', 'website'), ('phone', 'phone'),
              ('mobile', 'mobile'), ('fax', 'fax'), ('email', 'email'),
              ('comment', 'comment'), ('supplier', 'supplier'),
              ('customer', 'customer'), ('ref', 'ref'), ('lang', 'lang'),
              ('date', 'date'), ('notify_email', 'notify_email'),
              ('type','type')]

    @mapping
    def country_id(self, record):

        if not record.get('country_id'):
            return
        country = self.env['res.country'].search(
            [('name', '=', record['country_id'][1])],
            limit=1
        )
        if country:
            return {'country_id': country.id}

    @mapping
    def state_id(self, record):

        if not record.get('state_id'):
            return
        state = self.env['res.country.state'].search(
            [('name', '=', record['state_id'][1])],
            limit=1
        )
        if state:
            return {'state_id': state.id}

    @mapping
    def property_account_position(self, record):

        if not record.get('property_account_position'):
            return
        fiscal_position = self.env['account.fiscal.position'].search(
            [('name', '=', record['property_account_position'][1])],
            limit=1
        )
        if fiscal_position:
            return {'property_account_position': fiscal_position.id}

    @mapping
    def property_pricelist_id(self,record):
        binder = self.binder_for('odooconnector.product.pricelist')
        pricelist_id = binder.to_openerp(record['property_pricelist_id'][0], wrap=True)
        if pricelist_id:
            return {'property_product_pricelist': pricelist_id}

    @mapping
    def parent_id(self,record):
        if record.get('parent_id'):
            binder = self.binder_for('odooconnector.res.partner')
            parent_id = binder.to_openerp(record['parent_id'][0], wrap=True)
            if parent_id:
                return {'parent_id': parent_id}


@oc_odoo
class PartnerExporter(OdooExporter):
    _model_name = ['odooconnector.res.partner']

    def _get_remote_model(self):
        return 'res.partner'

    def _pre_export_check(self, record):
        if not self.backend_record.default_export_partner:
            return False

        domain = self.backend_record.default_export_partner_domain
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
                model_name='odooconnector.res.partner',
                context={'connector_no_export': True}
            )


@oc_odoo
class PartnerExportMapper(ExportMapper):
    _model_name = 'odooconnector.res.partner'

    direct = [('name', 'name'), ('is_company', 'is_company'),
              ('street', 'street'), ('street2', 'street2'), ('city', 'city'),
              ('zip', 'zip'), ('website', 'website'), ('phone', 'phone'),
              ('mobile', 'mobile'), ('fax', 'fax'), ('email', 'email'),
              ('comment', 'comment'), ('supplier', 'supplier'),
              ('customer', 'customer'), ('ref', 'ref'), ('lang', 'lang'),
              ('date', 'date'), ('notify_email', 'notify_email'),
              ('type','type')]

    @mapping
    def property_pricelist_id(self,record):
        binder = self.binder_for('odooconnector.product.pricelist')
        pricelist_id = binder.to_backend(record.openerp_id.property_product_pricelist.id, wrap=True)
        if pricelist_id:
            return {'property_product_pricelist': pricelist_id}

    @mapping
    def parent_id(self,record):
        if record.openerp_id.parent_id:
            binder = self.binder_for('odooconnector.res.partner')
            parent_id = binder.to_backend(record.openerp_id.parent_id.id, wrap=True)
            print"parent_idparent_idparent_id",parent_id
            if parent_id:
                return {'parent_id': parent_id}

    @mapping
    def country_id(self,record):
        if record.openerp_id.country_id:
            adapter = self.unit_for(OdooAdapter)
            country_id = adapter.search([
                ('name', '=', record.openerp_id.country_id.name)],
                                    model_name='res.country')
            if country_id:
                return {'country_id': country_id[0]}

    @mapping
    def country_id(self,record):
        if record.openerp_id.country_id:
            adapter = self.unit_for(OdooAdapter)
            country_id = adapter.search([
                ('name', '=', record.openerp_id.country_id.name)],
                                    model_name='res.country')
            if country_id:
                return {'country_id': country_id[0]}

    @mapping
    def state_id(self,record):
        if record.openerp_id.state_id:
            adapter = self.unit_for(OdooAdapter)
            state_id = adapter.search([
                ('name', '=', record.openerp_id.state_id.name)],
                                    model_name='res.country.state')
            if state_id:
                return {'state_id': state_id[0]}

    @mapping
    def property_account_position(self,record):
        if record.openerp_id.property_account_position:
            adapter = self.unit_for(OdooAdapter)
            fiscal_id = adapter.search([
                ('name', '=', record.openerp_id.property_account_position.name)],
                                    model_name='account.fiscal.position')
            if fiscal_id:
                return {'property_account_position': fiscal_id[0]}

@oc_odoo
class PartnerBatchExporter(DirectBatchExporter):
    _model_name = ['odooconnector.res.partner']

    def _get_remote_model(self):
        return 'res.partner'

