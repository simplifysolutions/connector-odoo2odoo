# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector.unit.mapper import ImportMapper, ExportMapper
from ..unit.import_synchronizer import (OdooImporter, DirectBatchImporter)
from ..unit.export_synchronizer import (OdooExporter, TranslationExporter,
                                        AddCheckpoint)
from ..unit.mapper import (OdooImportMapper, OdooImportMapChild,
                           OdooExportMapChild)
from ..unit.backend_adapter import OdooAdapter
from ..backend import oc_odoo


_logger = logging.getLogger(__name__)


class OdooConnectorProductPricelistVersion(models.Model):
    _name = 'odooconnector.product.pricelist.version'
    _inherit = 'odooconnector.binding'
    _inherits = {'product.pricelist.version': 'openerp_id'}
    _description = 'Odoo Connector Product Pricelist Version'

    openerp_id = fields.Many2one(
        comodel_name='product.pricelist.version',
        string='Pricelist Version',
        required=True,
        ondelete='restrict'
    )


class OdooConnectorProductPricelistItem(models.Model):
    _name = 'odooconnector.product.pricelist.item'
    _inherit = 'odooconnector.binding'
    _inherits = {'product.pricelist.item': 'openerp_id'}
    _description = 'Odoo Connector Product Pricelist Version Items'

    openerp_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        string='Pricelist Version Items',
        required=True,
        ondelete='restrict'
    )


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.product.pricelist.item',
        inverse_name='openerp_id',
        string='Odoo Binding'
    )


@oc_odoo
class ProductPricelistVersionBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.product.pricelist.version']


@oc_odoo
class ProductPricelistVersionImporter(OdooImporter):
    _model_name = ['odooconnector.product.pricelist.version']


@oc_odoo
class ProductPricelistItemBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.product.pricelist.item']


@oc_odoo
class ProductPricelistItemImporter(OdooImporter):
    _model_name = ['odooconnector.product.pricelist.item']


@oc_odoo
class ProductPricelistVersionImportMapper(OdooImportMapper):
    _model_name = ['odooconnector.product.pricelist.version']

    _map_child_class = OdooImportMapChild


# We use the ImportMapper since the priceliste.partnerinfo is not part of
# a odooconnector binding model so far.
@oc_odoo
class ProductPricelistItemImportMapper(ImportMapper):
    _model_name = ['product.pricelist.item']

    direct = [('name', 'name'), ('min_quantity', 'min_quantity'),
              ('sequence', 'sequence')]


@oc_odoo
class ProductPricelistVersionExportMapper(ExportMapper):
    _model_name = ['odooconnector.product.pricelist.version']
    _map_child_class = OdooExportMapChild

    direct = [('name', 'name'), ('date_start', 'date_start'),
              ('date_end', 'date_end')
              ]


@oc_odoo
class ProductPricelistItemTranslationExporter(TranslationExporter):
    _model_name = ['odooconnector.product.pricelist.item']


@oc_odoo
class ProductPricelistItemTranslationExportMapper(ExportMapper):
    _model_name = ['odooconnector.product.pricelist']
    direct = [('name', 'name')]


@oc_odoo
class ProductPricelistItemExportMapper(ExportMapper):
    _model_name = ['odooconnector.product.pricelist.item']
    _map_child_class = OdooExportMapChild

    direct = [('min_quantity', 'min_quantity'), ]

    @mapping
    def product_id(self, record):
        if record.product_id:
            binder = self.binder_for('odooconnector.product.product')
            product_id = binder.to_backend(record.product_id.id, wrap=True)
            return {'product_id': product_id,
                    'applied_on': '0_product_variant'}

    @mapping
    def date_start(self, record):
        return {'date_start': record.price_version_id.date_start}

    @mapping
    def date_end(self, record):
        return {'date_end': record.price_version_id.date_end}

    @mapping
    def price_discount(self, record):
        if record.base == 1 and round(record.price_discount, 2) <= -1.00:
            return {
                'compute_price': 'fixed',
                'fixed_price': record.price_surcharge or 0
            }


@oc_odoo
class ProductPricelistItemExporter(OdooExporter):
    _model_name = ['odooconnector.product.pricelist.item']
    _base_mapper = ProductPricelistItemExportMapper

    def _get_remote_model(self):
        return 'product.pricelist.item'

    def _pre_export_check(self, record):
        """ Run some checks before exporting the record """
        if not self.backend_record.default_export_product_pricelist:
            return False
        if record.openerp_id.base == 1 and round(
                record.openerp_id.price_discount, 2) != -1.00:
            checkpoint = self.unit_for(AddCheckpoint)
            checkpoint.run(record.id)
        domain = self.backend_record.default_export_product_pricelist_domain
        return self._pre_export_domain_check(record, domain)

    def _after_export(self, record_created):
        _logger.debug('Product Pricelist exporter: _after_export called')

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
                model_name='odooconnector.product.pricelist.item',
                context={'connector_no_export': True}
            )
