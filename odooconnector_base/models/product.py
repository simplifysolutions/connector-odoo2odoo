# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping, ExportMapper)

from ..unit.import_synchronizer import (OdooImporter, DirectBatchImporter,
                                        TranslationImporter)
from ..unit.export_synchronizer import (OdooExporter, TranslationExporter)
from ..unit.delete_synchronizer import (OdooDeleter)
from ..unit.mapper import (OdooImportMapper, OdooImportMapChild,
                           OdooExportMapChild)
from ..unit.backend_adapter import OdooAdapter
from ..backend import oc_odoo
from . product_uom import ProductUomExporter


_logger = logging.getLogger(__name__)


class OdooConnectorProductTemplate(models.Model):
    _name = 'odooconnector.product.product'
    _inherit = 'odooconnector.binding'
    _inherits = {'product.product': 'openerp_id'}
    _description = 'Odoo Connector Product'

    openerp_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='cascade'
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.product.product',
        inverse_name='openerp_id',
        string='Odoo Connector Bindings'
    )


@oc_odoo
class ProductBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.product.product']


@oc_odoo
class ProductTranslationImporter(TranslationImporter):
    _model_name = ['odooconnector.product.product']


@oc_odoo
class ProductImportMapper(OdooImportMapper):
    _model_name = ['odooconnector.product.product']
    _map_child_class = OdooImportMapChild

    direct = [('name', 'name'),
              # ('name_template', 'name_template'),
              ('type', 'type'),
              ('purchase_ok', 'purchase_ok'),
              ('sale_ok', 'sale_ok'),
              ('lst_price', 'list_price'),
              ('active', 'active'),
              ('standard_price', 'standard_price'),
              ('ean13', 'barcode'),
              ('default_code', 'default_code'),
              ('description', 'description'),
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

    @mapping
    def categ_id(self, record):
        if not record.get('categ_id'):
            return
        category = self.env['product.category'].search(
            [('name', '=', record['categ_id'][1])],
            limit=1
        )
        if category:
            return {'categ_id': category.id}

@oc_odoo
class ProductSimpleImportMapper(OdooImportMapper):
    _model_name = ['odooconnector.product.product']

    direct = [('name', 'name'),
              # ('name_template', 'name_template'),
              ('description', 'description'),
              ]


@oc_odoo
class ProductImporter(OdooImporter):
    _model_name = ['odooconnector.product.product']

    # We have to set a explicit mapper since there are two different
    # mappers that might match
    _base_mapper = ProductImportMapper

    def _after_import(self, binding):
        _logger.debug('Product Importer: _after_import called')
        translation_importer = self.unit_for(TranslationImporter)
        translation_importer.run(
            self.external_id,
            binding.id,
            mapper_class=ProductSimpleImportMapper
        )

    def _is_uptodate(self, binding):
        res = super(ProductImporter, self)._is_uptodate(binding)

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


@oc_odoo
class ProductImportChildMapper(OdooImportMapChild):
    _model_name = ['odooconnector.product.supplierinfo']


@oc_odoo
class ProductExportMapper(ExportMapper):
    _model_name = ['odooconnector.product.product']
    _map_child_class = OdooExportMapChild

    direct = [('name', 'name'),
              # ('name_template', 'name_template'),
              ('sale_ok', 'sale_ok'),
              ('purchase_ok', 'purchase_ok'),
              ('lst_price', 'lst_price'),
              ('active', 'active'),
              ('standard_price', 'standard_price'),
              ('ean13', 'barcode'),
              ('default_code', 'default_code'),
              ('description', 'description'),
              ]

    children = [
        ('seller_ids', 'seller_ids', 'odooconnector.product.supplierinfo')
    ]

    @mapping
    def type(self, record):
        return {'type': 'service'}

    @mapping
    def uom_id(self, record):
        if not record.uom_id.id:
            return
        uom_id = self._uom_search(record.uom_id)
        if uom_id:
            return {'uom_id': uom_id}

    @mapping
    def uom_po_id(self, record):
        if not record.uom_po_id.id:
            return
        uom_id = self._uom_search(record.uom_po_id)
        if uom_id:
            return {'uom_po_id': uom_id}

    def _uom_search(self, uom_id):
        """Search for a uom

        :returns: uom id or None
        """
        # TODO: Unnecessary round trip ...
        product_uom = self.binder_for('odooconnector.product.uom').to_backend(
            uom_id.id,
            wrap=True
        )
        if product_uom:
            return product_uom

    @mapping
    def categ_id(self,record):
        if not record.categ_id:
            return

        adapter = self.unit_for(OdooAdapter)
        categ_id = adapter.search([('name', '=', record.categ_id.name)],
                                     model_name='product.category')
        if not categ_id:
            categ_id = adapter.create({'name': record.categ_id.name},
                                         model_name='product.category')
        if isinstance(categ_id, list):
            categ_id = categ_id[0]
        return {'categ_id': categ_id}


@oc_odoo
class ProductTranslationExporter(TranslationExporter):
    _model_name = ['odooconnector.product.product']


# TODO(MJ): Instead of definining a specific translation mapper for each model
#           a special translation mapper should be used that create the list
#           of direct fields dynamically based on a given list of fields,
#           e.g. the list of translatable fields.
@oc_odoo
class ProductTranslationExportMapper(ExportMapper):
    _model_name = ['odooconnector.product.product']
    direct = [('name', 'name'),
              ('name_template', 'name_template'),
              ('description', 'description'),
              ]


@oc_odoo
class ProductExporter(OdooExporter):
    _model_name = ['odooconnector.product.product']
    _base_mapper = ProductExportMapper

    def _get_remote_model(self):
        return 'product.product'

    def _pre_export_check(self, record):
        """ Run some checks before exporting the record """
        if not self.backend_record.default_export_product:
            return False

        domain = self.backend_record.default_export_product_domain
        return self._pre_export_domain_check(record, domain)

    def _after_export(self, record_created):
        _logger.debug('Product exporter: _after_export called')
        translations_exporter = self.unit_for(TranslationExporter)
        translations_exporter.run(
            self.external_id,
            self.binding_id,
            mapper_class=ProductTranslationExportMapper)

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
                model_name='odooconnector.product.product',
                context={'connector_no_export': True}
            )

#    def _export_dependencies(self):
#        record = self.model.browse(self.binding_id)
#        product_uom = self.binder_for('odooconnector.product.uom').to_backend(
#        record.openerp_id.uom_id.id,
#        wrap=True
#        )
#        if not product_uom:
#            relation = (record.openerp_id.uom_id)
#            self._export_dependency(relation, 'odooconnector.product.uom',
#                                exporter_class=ProductUomExporter)


@oc_odoo
class ProductDeleter(OdooDeleter):
    _model_name = ['odooconnector.product.product']

    def _get_remote_model(self):
        return 'product.product'