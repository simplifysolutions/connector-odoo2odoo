# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp import models, fields, api
from openerp.addons.connector.unit.mapper import (mapping, ExportMapper)

from ..unit.import_synchronizer import (OdooImporter, DirectBatchImporter,
                                        TranslationImporter)
from ..unit.export_synchronizer import (OdooExporter, TranslationExporter)
from ..unit.mapper import (OdooImportMapper, OdooImportMapChild,
                           OdooExportMapChild)
from ..unit.backend_adapter import OdooAdapter
from ..backend import oc_odoo


_logger = logging.getLogger(__name__)


class OdooConnectorProductTemplate(models.Model):
    _name = 'odooconnector.product.pricelist'
    _inherit = 'odooconnector.binding'
    _inherits = {'product.pricelist': 'openerp_id'}
    _description = 'Odoo Connector Product Pricelist'

    openerp_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Product Pricelist',
        required=True,
        ondelete='restrict'
    )


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.one
    def _get_item_ids(self):
        self.version_item_ids = self.env['product.pricelist.item'].search([
            ('price_version_id', 'in', self.version_id.ids),
        ])

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.product.pricelist',
        inverse_name='openerp_id',
        string='Odoo Connector Bindings'
    )
    version_item_ids = fields.One2many(comodel_name="product.pricelist.item",
                                       compute=_get_item_ids,
                                       # _inverse_name='pricelist_id',
                                       string="Rules", required=False, )


@oc_odoo
class ProductPricelistBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.product.pricelist']


@oc_odoo
class ProductPricelistTranslationImporter(TranslationImporter):
    _model_name = ['odooconnector.product.pricelist']


@oc_odoo
class ProductPricelistImportMapper(OdooImportMapper):
    _model_name = ['odooconnector.product.pricelist']
    _map_child_class = OdooImportMapChild

    direct = [
        ('name', 'name'),
        ('active', 'active')
    ]

    children = [
        # ('seller_ids', 'seller_ids', 'odooconnector.product.supplierinfo'),
    ]

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        source = map_record.source
        child_records = source[from_attr]

        detail_records = []
        _logger.debug('Loop over product children ...')
        for child_record in child_records:
            adapter = self.unit_for(OdooAdapter, model_name)

            detail_record = adapter.read(child_record)
            detail_records.append(detail_record)

        mapper = self._get_map_child_unit(model_name)

        items = mapper.get_items(
            detail_records, map_record, to_attr, options=self.options
        )

        _logger.debug('Product child "%s": %s', model_name, items)

        return items

    @mapping
    def uom_id(self, record):

        if not record.get('uom_id'):
            return

        uom = self.env['product.uom'].search(
            [('name', '=', record['uom_id'][1])],
            limit=1
        )

        if uom:
            return {'uom_id': uom.id}

    @mapping
    def uom_po_id(self, record):

        if not record.get('uom_id'):
            return

        uom = self.env['product.uom'].search(
            [('name', '=', record['uom_po_id'][1])],
            limit=1
        )

        if uom:
            return {'uom_po_id': uom.id}


@oc_odoo
class ProductPricelistSimpleImportMapper(OdooImportMapper):
    _model_name = ['odooconnector.product.pricelist']

    direct = [('name', 'name'),
              # ('name_template', 'name_template'),
              # ('description', 'description')
              ]


@oc_odoo
class ProductPricelistImporter(OdooImporter):
    _model_name = ['odooconnector.product.pricelist']

    # We have to set a explicit mapper since there are two different
    # mappers that might match
    _base_mapper = ProductPricelistImportMapper

    def _after_import(self, binding):
        _logger.debug('Product Importer: _after_import called')
        translation_importer = self.unit_for(TranslationImporter)
        translation_importer.run(
            self.external_id,
            binding.id,
            mapper_class=ProductPricelistSimpleImportMapper
        )

    def _is_uptodate(self, binding):
        res = super(ProductPricelistImporter, self)._is_uptodate(binding)

        if res:
            _logger.debug('Check also the last product.template write date...')
            product_tmpl_id = self.external_record['product_tmpl_id'][0]
            product_tmpl = self.backend_adapter.read(
                product_tmpl_id, model_name='product.template')
            if product_tmpl:
                date_from_string = fields.Datetime.from_string
                sync_date = date_from_string(binding.sync_date)
                external_date = date_from_string(product_tmpl['write_date'])

                return external_date < sync_date

        return res


# @oc_odoo
# class ProductPricelistImportChildMapper(OdooImportMapChild):
#     _model_name = ['odooconnector.product.supplierinfo']


@oc_odoo
class ProductPricelistExportMapper(ExportMapper):
    _model_name = ['odooconnector.product.pricelist']
    _map_child_class = OdooExportMapChild

    direct = [('name', 'name'),
              ('active', 'active')
              ]

    children = [
        ('version_item_ids', 'item_ids',
         'odooconnector.product.pricelist.item')
    ]

    @mapping
    def currency_id(self, record):
        if not record.currency_id:
            return
        adapter = self.unit_for(OdooAdapter)
        currency_id = adapter.search([
            ('name', '=', record.currency_id.name)],
            model_name='res.currency')
        if currency_id:
            return {'currency_id': currency_id[0]}


@oc_odoo
class ProductPricelistTranslationExporter(TranslationExporter):
    _model_name = ['odooconnector.product.pricelist']


# TODO(MJ): Instead of definining a specific translation mapper for each model
#           a special translation mapper should be used that create the list
#           of direct fields dynamically based on a given list of fields,
#           e.g. the list of translatable fields.
@oc_odoo
class ProductPricelistTranslationExportMapper(ExportMapper):
    _model_name = ['odooconnector.product.pricelist']
    direct = [('name', 'name'),
              # ('name_template', 'name_template'),
              # ('description', 'description')
              ]


@oc_odoo
class ProductPricelistExporter(OdooExporter):
    _model_name = ['odooconnector.product.pricelist']
    _base_mapper = ProductPricelistExportMapper

    def _get_remote_model(self):
        return 'product.pricelist'

    def _pre_export_check(self, record):
        """ Run some checks before exporting the record """
        if not self.backend_record.default_export_product_pricelist:
            return False
        domain = self.backend_record.default_export_product_pricelist_domain
        return self._pre_export_domain_check(record, domain)

    def _after_export(self, record_created):
        _logger.debug('Product Pricelist exporter: _after_export called')
        translations_exporter = self.unit_for(TranslationExporter)
        translations_exporter.run(
            self.external_id,
            self.binding_id,
            mapper_class=ProductPricelistTranslationExportMapper)

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
                model_name='odooconnector.product.pricelist',
                context={'connector_no_export': True}
            )
