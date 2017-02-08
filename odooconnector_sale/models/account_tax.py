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


class OdooConnectorAccountTax(models.Model):
    _name = 'odooconnector.account.tax'
    _inherit = 'odooconnector.binding'
    _inherits = {'account.tax': 'openerp_id'}
    _description = 'Odoo Connector Account Tax'

    openerp_id = fields.Many2one(
        comodel_name='account.tax',
        string='Account Tax',
        required=True,
        ondelete='restrict'
    )


class AccountTax(models.Model):
    _inherit = 'account.tax'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.account.tax',
        inverse_name='openerp_id',
        string='Odoo Binding'
    )


@oc_odoo
class AccountTaxBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.account.tax']


@oc_odoo
class AccountTaxImporter(OdooImporter):
    _model_name = ['odooconnector.account.tax']


@oc_odoo
class AccountTaxImporterMapper(OdooImportMapper):
    _model_name = ['odooconnector.account.tax']

    direct = [
        ('name', 'name'), ('description', 'description'), ('type', 'type'),
    ]

    @mapping
    def amount(self, record):
        if not record.get('amount'):
            return
        amount = record.get('amount')
        if record.get('type') == "percent":
            amount = amount / 100
        return {'amount': amount}

    @mapping
    def parent_id(self, record):
        if record.get('parent_id'):
            binder = self.binder_for('odooconnector.account.tax')
            parent_id = binder.to_openerp(record['parent_id'][0], unwrap=True)
            if parent_id:
                return {'parent_id': parent_id}


@oc_odoo
class AccountTaxExporter(OdooExporter):
    _model_name = ['odooconnector.account.tax']

    def _get_remote_model(self):
        return 'account.tax'

    def _pre_export_check(self, record):
        if not record.external_id:
            adapter = self.unit_for(OdooAdapter)
            tax_id = adapter.search([('name', '=', record.openerp_id.name)],
                                    model_name='account.tax')
            if tax_id:
                record.write({'external_id': tax_id[0]})
        if not self.backend_record.default_export_product_uom:
            return False
        domain = self.backend_record.default_export_product_uom_domain
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
                model_name='odooconnector.account.tax',
                context={'connector_no_export': True}
            )


@oc_odoo
class AccountTaxExporterMapper(ExportMapper):
    _model_name = ['odooconnector.account.tax']

    direct = [
        ('name', 'name'), ('description', 'description'),
    ]

    @mapping
    def type(self, record):
        if record.child_depend:
            type = 'group'
        elif record.price_include:
            type = 'division'
        else:
            type = record.type
        return {'amount_type': type}

    @mapping
    def amount(self, record):
        tax = record.openerp_id
        amount = tax.amount
        if tax.type == "percent":
            amount = amount * 100
        return {'amount': amount}

#    @mapping
#    def parent_id(self, record):
#        if record.parent_id:
#            binder = self.binder_for('odooconnector.account.tax')
#            parent_id = binder.to_backend(
#                record.parent_id.id, wrap=True)
#            print"parent_idparent_idparent_id", parent_id
#            if parent_id:
#                return {'parent_id': parent_id}

    @mapping
    def children_tax_ids(self, record):
        if record.child_ids:
            child_tax_ids = []
            binder = self.binder_for('odooconnector.account.tax')
            for each_line in record.child_ids:
                tax_id = binder.to_backend(each_line.id, wrap=True)
                if tax_id:
                    child_tax_ids.append(tax_id)
            return {'children_tax_ids': [(6, 0, child_tax_ids)]}
