# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

from openerp import models, fields, api
from openerp.addons.odooconnector_base.backend import oc_odoo
from openerp.addons.odooconnector_base.unit.backend_adapter import OdooAdapter
from openerp.addons.odooconnector_base.unit.import_synchronizer import (
    OdooImporter, DirectBatchImporter)
from openerp.addons.connector.unit.mapper import (ExportMapper, ImportMapper,
                                                  mapping)
from openerp.addons.connector.exception import MappingError
from openerp.addons.odooconnector_base.unit.mapper import (
    OdooExportMapChild, OdooImportMapChild, OdooImportMapper)
from openerp.addons.odooconnector_base.unit.export_synchronizer import (
    OdooExporter)
from openerp.addons.odooconnector_base.unit.import_synchronizer import import_record
from ..unit.mapper import (OdooExportMapSaleChild, OdooImportMapSaleChild)
import logging
_logger = logging.getLogger(__name__)

"""

Sale
========

All implementations specific related to the export / import / mapping etc.
of sale order objects.

"""
ORDER_STATUS_MAPPING_8_to_10 = {
    'draft': 'draft',
    'sent': 'sent',
    'cancel': 'cancel',
    'manual': 'sale',
    'progress': 'sale',
    'shipping_except': 'sale',
    'invoice_except': 'sale',
    'waiting_date': 'sale',
    'done': 'done',
}

ORDER_STATUS_MAPPING_10_to_8 = {
    'draft': 'draft',
    'sent': 'sent',
    'cancel': 'cancel',
    'sale': 'progress',
    'done': 'done',
}


class OdooConnectorSaleOrder(models.Model):
    _name = 'odooconnector.sale.order'
    _inherit = 'odooconnector.binding'
    _inherits = {'sale.order': 'openerp_id'}
    _description = 'Odoo Connector sale Order'

    openerp_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='restrict'
    )
    odooconnector_order_line_ids = fields.One2many(
        comodel_name='odooconnector.sale.order.line',
        inverse_name='odooconnector_order_id',
        string='Odooconnector Order Lines'
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.sale.order',
        inverse_name='openerp_id',
        string='Odoo Binding'
    )


class OdooConnectorSaleOrderLine(models.Model):
    _name = 'odooconnector.sale.order.line'
    _inherit = 'odooconnector.binding'
    _inherits = {'sale.order.line': 'openerp_id'}
    _description = 'Odoo Connector Sale Order Line'

    odooconnector_order_id = fields.Many2one(
        comodel_name='odooconnector.sale.order',
        string='Odooconnector Sale Order',
        required=True,
        ondelete='cascade',
        select=True)
    openerp_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Order Line',
        required=True,
        ondelete='restrict'
    )

    @api.model
    def create(self, vals):
        if vals.get('odooconnector_order_id'):
            odooconnector_order_id = vals['odooconnector_order_id']
            binding = self.env['odooconnector.sale.order'].browse(
                odooconnector_order_id)
            vals['order_id'] = binding.openerp_id.id
        binding = super(OdooConnectorSaleOrderLine, self).create(vals)
        return binding


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.sale.order.line',
        inverse_name='openerp_id',
        string='Odoo Binding'
    )


@oc_odoo
class SaleOrderImporter(DirectBatchImporter):
    _model_name = ['odooconnector.sale.order']

    # to create job while importing records
    def _import_record(self, record_id, api=None):
        """ Import record directly """
        import_record.delay(self.session, self.model._name,
                            self.backend_record.id, record_id)


@oc_odoo
class SaleOrderImporter(OdooImporter):
    _model_name = ['odooconnector.sale.order']

    def _import_dependencies(self):
        record = self.external_record

        if record.get('partner_id'):
            binder = self.binder_for('odooconnector.res.partner')
            partner_id = binder.to_openerp(
                record['partner_id'][0], unwrap=True)
            if not partner_id:
                self._import_dependency(record['partner_id'][0],
                                        'odooconnector.res.partner')
#        if record.get('pricelist_id'):
#            binder = self.binder_for('odooconnector.product.pricelist')
#            pricelist_id = binder.to_openerp(record['pricelist_id'][0], unwrap=True)
#            if not pricelist_id:
#                self._import_dependency(record['pricelist_id'][0],
#                                        'odooconnector.product.pricelist')


@oc_odoo
class SaleOrderImportMapper(OdooImportMapper):
    _model_name = 'odooconnector.sale.order'
    _map_child_class = OdooImportMapSaleChild

    direct = [('date_order', 'date_order'),
              ('origin', 'origin'),
              ('client_order_ref', 'client_order_ref'),
              ('note', 'note'),
              ('picking_policy', 'picking_policy'),
              ]

    children = [
        ('order_line', 'odooconnector_order_line_ids',
         'odooconnector.sale.order.line')
    ]

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        source = map_record.source
        child_records = source[from_attr]
        detail_records = []
        _logger.debug('Loop over order lines...')
        for child_record in child_records:
            adapter = self.unit_for(OdooAdapter, model_name)
            detail_record = adapter.read(child_record)[0]
            detail_records.append(detail_record)
        mapper = self._get_map_child_unit(model_name)
        items = mapper.get_items(
            detail_records, map_record, to_attr, options=self.options
        )
        _logger.debug('Order lines "%s": %s', model_name, items)
        return items

    @mapping
    def partner_id(self, record):
        binder = self.binder_for('odooconnector.res.partner')
        partner_id = binder.to_openerp(record['partner_id'][0], unwrap=True)
        assert partner_id is not None, (
            "partner_id %s should have been imported in "
            "SaleOrderImporter._import_dependencies" % record['partner_id'])
        return {'partner_id': partner_id}

    @mapping
    def partner_invoice_id(self, record):
        binder = self.binder_for('odooconnector.res.partner')
        partner_invoice_id = binder.to_openerp(
            record['partner_invoice_id'][0], unwrap=True)
        assert partner_invoice_id is not None, (
            "partner_invoice_id %s should have been imported in "
            "SaleOrderImporter._import_dependencies" %
            record['partner_invoice_id'])
        return {'partner_invoice_id': partner_invoice_id}

    @mapping
    def partner_shipping_id(self, record):
        binder = self.binder_for('odooconnector.res.partner')
        partner_shipping_id = binder.to_openerp(
            record['partner_shipping_id'][0], unwrap=True)
        assert partner_shipping_id is not None, (
            "partner_shipping_id %s should have been imported in "
            "SaleOrderImporter._import_dependencies" %
            record['partner_shipping_id'])
        return {'partner_shipping_id': partner_shipping_id}

    @mapping
    def pricelist_id(self, record):
        binder = self.binder_for('odooconnector.product.pricelist')
        pricelist_id = binder.to_openerp(
            record['pricelist_id'][0], unwrap=True)
        if pricelist_id:
            return {'pricelist_id': pricelist_id}

    @mapping
    def section_id(self, record):
        if not record.get('team_id'):
            return
        binder = self.binder_for('odooconnector.crm.case.section')
        section_id = binder.to_openerp(record['team_id'][0], unwrap=True)
        if section_id:
            return {'section_id': section_id}

    @mapping
    def user_id(self, record):
        if not record.get('user_id'):
            return
        binder = self.binder_for('odooconnector.res.users')
        user_id = binder.to_openerp(record['user_id'][0], unwrap=True)
        if user_id:
            return {'user_id': user_id}

#    @mapping
#    def warehouse_id(self, record):
#        if not record.get('warehouse_id'):
#            return
#        warehouse = self.env['stock.warehouse'].search(
#            [('name', '=', record['warehouse_id'][1])],
#            limit=1)
#        if warehouse:
#            return {'warehouse_id': warehouse.id}

    @mapping
    def currency_id(self, record):
        if not record.get('currency_id'):
            return
        currency = self.env['res.currency'].search(
            [('name', '=', record['currency_id'][1])],
            limit=1)
        if currency:
            return {'currency_id': currency.id}

    @mapping
    def fiscal_position_id(self, record):
        if not record.get('fiscal_position_id'):
            return
        fiscal_position = self.env['account.fiscal.position'].search(
            [('name', '=', record['fiscal_position_id'][1])],
            limit=1)
        if fiscal_position:
            return {'fiscal_position': fiscal_position.id}

    @mapping
    def company_id(self, record):
        if not record.get('company_id'):
            return
        company = self.env['res.company'].search(
            [('name', '=', record['company_id'][1])],
            limit=1)
        if company:
            return {'company_id': company.id}

    @mapping
    def payment_term_id(self, record):
        if not record.get('payment_term_id'):
            return
        payment_term = self.env['account.payment.term'].search(
            [('name', '=', record['payment_term_id'][1])],
            limit=1)
        if payment_term:
            return {'payment_term': payment_term.id}

    @mapping
    def incoterm(self, record):
        if not record.get('incoterm'):
            return
        incoterm = self.env['stock.incoterms'].search(
            [('name', '=', record['incoterm'][1])],
            limit=1)
        if incoterm:
            return{'incoterm': incoterm.id}

    @mapping
    def campaign_id(self, record):
        if not record.get('campaign_id'):
            return
        campaign = self.env['crm.tracking.campaign'].search(
            [('name', '=', record['campaign_id'][1])],
            limit=1)
        if campaign:
            return {'campaign_id': campaign.id}

    @mapping
    def medium_id(self, record):
        if not record.get('medium_id'):
            return
        medium = self.env['crm.tracking.medium'].search(
            [('name', '=', record['medium_id'][1])],
            limit=1)
        if medium:
            return{'medium_id': medium.id}

    @mapping
    def source_id(self, record):
        if not record.get('source_id'):
            return
        source = self.env['crm.tracking.source'].search(
            [('name', '=', record['source_id'][1])],
            limit=1)
        if source:
            return{'source_id': source.id}

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

    @mapping
    def order_policy(self, record):
        return{'order_policy': 'picking'}

    @mapping
    def picking_policy(self, record):
        return{'picking_policy': 'direct'}

    @mapping
    def state(self, record):
        state = ORDER_STATUS_MAPPING_10_to_8[record['state']]
        return {'state': state}


@oc_odoo
class SaleOrderLineBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.sale.order.line']


@oc_odoo
class SaleOrderLineImporter(OdooImporter):
    _model_name = ['odooconnector.sale.order.line']


@oc_odoo
class SaleOrderLineImportMapper(OdooImportMapper):
    _model_name = 'odooconnector.sale.order.line'
    _map_child_class = OdooImportMapChild

    direct = [
        ('name', 'name'),
        ('price_unit', 'price_unit'),
        ('product_uom_qty', 'product_uom_qty'),
    ]

    @mapping
    def line_id(self, record):
        binder = self.binder_for('odooconnector.sale.order.line')
        line_id = binder.to_openerp(record['id'])
        if line_id:
            # id is of odooconnector.sale.order.line record
            return {'id': line_id}

    @mapping
    def external_id(self, record):
        return {'external_id': record.get('id')}

    @mapping
    def product_id(self, record):
        binder = self.binder_for('odooconnector.product.product')
        product_id = binder.to_openerp(record['product_id'][0], unwrap=True)
        if product_id:
            return {'product_id': product_id}

    @mapping
    def product_uom(self, record):
        if not record.get('product_uom'):
            return
        product_uom = self.env['product.uom'].search(
            [('name', '=', record['product_uom'][1])],
            limit=1)
        if product_uom:
            return{'product_uom': product_uom.id}

    @mapping
    def tax_id(self, record):
        if not record.get('tax_id'):
            return
        tax_ids = []
        binder = self.binder_for('odooconnector.account.tax')
        for each_tax in record.get('tax_id'):
            tax_id = binder.to_openerp(each_tax, unwrap=True)
            if tax_id:
                tax_ids.append(tax_id)
        return {'tax_id': [(6, 0, tax_ids)]}

    @mapping
    def order_id(self, record):
        binder = self.binder_for('odooconnector.sale.order')
        order_id = binder.to_openerp(record['order_id'][0], unwrap=True)
        if order_id:
            return {'order_id': order_id}


@oc_odoo
class SaleOrderExporter(OdooExporter):
    _model_name = 'odooconnector.sale.order'

    def _get_remote_model(self):
        return 'sale.order'

    def _pre_export_check(self, record):
        binder = self.binder_for('odooconnector.res.partner')

        if record.partner_id:
            partner_id = binder.to_backend(
                record.partner_id.id, wrap=True)
            if not partner_id:
                return False
        if record.partner_invoice_id:
            partner_invoice_id = binder.to_backend(
                record.partner_invoice_id.id, wrap=True)
            if not partner_invoice_id:
                return False
        if record.partner_shipping_id:
            partner_shipping_id = binder.to_backend(
                record.partner_shipping_id.id, wrap=True)
            if not partner_shipping_id:
                return False
        if not self.backend_record.default_export_sale_order:
            return False
        domain = self.backend_record.default_export_so_domain
        return self._pre_export_domain_check(record, domain)

    def _after_export(self, record_created):
        # create a ic_binding in the backend, indicating that the sale order
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
                model_name='odooconnector.sale.order',
                context={'connector_no_export': True}
            )
        binding = self.env[self._model_name].browse(self.binding_id)
        conn_order_line = self.env['odooconnector.sale.order.line']
        for each in binding.order_line:
            if not each.oc_bind_ids:
                vals = {
                    'backend_id': binding.backend_id.id,
                    'openerp_id': each.id,
                    'odooconnector_order_id': binding.id,
                    'exported_record': True,
                    'order_id': binding.openerp_id.id,
                }
                conn_order_line.create(vals)


@oc_odoo
class SaleOrderLineExporter(OdooExporter):
    _model_name = ['odooconnector.sale.order.line']

    def _get_remote_model(self):
        return 'sale.order.line'

    def _pre_export_check(self, record):
        binder = self.binder_for('odooconnector.product.product')
        if record.product_id:
            product_id = binder.to_backend(
                record.product_id.id, wrap=True)
            if not product_id:
                return False
        if record.order_id:
            order_id = self.binder_for('odooconnector.sale.order').to_backend(
                record.order_id.id, wrap=True)
            if not order_id:
                return False
        if not self.backend_record.default_export_sale_order:
            return False
        return True

    def _after_export(self, record_created):
        # create a ic_binding in the backend, indicating that the order line
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
                model_name='odooconnector.sale.order.line',
                context={'connector_no_export': True}
            )


@oc_odoo
class SaleOrderExportMapper(ExportMapper):
    _model_name = ['odooconnector.sale.order']
    _map_child_class = OdooExportMapSaleChild

    direct = [
        ('date_order', 'date_order'),
        ('origin', 'origin'),
        ('client_order_ref', 'client_order_ref'),
        ('note', 'note'),
        ('picking_policy', 'picking_policy'),
    ]

#    children = [
#        ('odooconnector_order_line_ids', 'order_line', 'odooconnector.sale.order.line')
#    ]

    @mapping
    def partner_id(self, record):
        if record.partner_id:
            binder = self.binder_for('odooconnector.res.partner')
            partner_id = binder.to_backend(record.partner_id.id, wrap=True)
            return {'partner_id': partner_id}

    @mapping
    def partner_invoice_id(self, record):
        if record.partner_invoice_id:
            binder = self.binder_for('odooconnector.res.partner')
            partner_invoice_id = binder.to_backend(
                record.partner_invoice_id.id, wrap=True)
            return {'partner_invoice_id': partner_invoice_id}

    @mapping
    def partner_shipping_id(self, record):
        if record.partner_shipping_id:
            binder = self.binder_for('odooconnector.res.partner')
            partner_shipping_id = binder.to_backend(
                record.partner_shipping_id.id, wrap=True)
            return {'partner_shipping_id': partner_shipping_id}

    @mapping
    def pricelist_id(self, record):
        binder = self.binder_for('odooconnector.product.pricelist')
        pricelist_id = binder.to_backend(record.pricelist_id.id, wrap=True)
        if pricelist_id:
            return {'pricelist_id': pricelist_id}

    # section_id is team_id  in v10
    @mapping
    def team_id(self, record):
        binder = self.binder_for('odooconnector.crm.case.section')
        team_id = binder.to_backend(record.section_id.id, wrap=True)
        if team_id:
            return {'team_id': team_id}

    @mapping
    def user_id(self, record):
        binder = self.binder_for('odooconnector.res.users')
        user_id = binder.to_backend(record.user_id.id, wrap=True)
        if user_id:
            return {'user_id': user_id}

    @mapping
    def fiscal_position_id(self, record):
        if record.fiscal_position:
            adapter = self.unit_for(OdooAdapter)
            fiscal_id = adapter.search([
                ('name', '=', record.fiscal_position.name)],
                model_name='account.fiscal.position')
            if fiscal_id:
                return {'fiscal_position_id': fiscal_id[0]}

    @mapping
    def payment_term_id(self, record):
        if record.payment_term:
            adapter = self.unit_for(OdooAdapter)
            payment_term_id = adapter.search([
                ('name', '=', record.payment_term.name)],
                model_name='account.payment.term')
            if payment_term_id:
                return {'payment_term_id': payment_term_id[0]}

    @mapping
    def state(self, record):
        state = ORDER_STATUS_MAPPING_8_to_10[record.state]
        return {'state': state}

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


@oc_odoo
class SaleOrderLineExportMapper(ExportMapper):
    _model_name = ['odooconnector.sale.order.line']

    direct = [
        ('name', 'name'),
        ('price_unit', 'price_unit'),
        ('product_uom_qty', 'product_uom_qty'),
    ]

    # doing mapping to update correct orderline record on v10
    @mapping
    def line_id(self, record):
        line_id = self.binder_for('odooconnector.sale.order.line').to_backend(
            record.id,
            wrap=True
        )
        if line_id:
            return {'id': line_id}

    @mapping
    def order_id(self, record):
        order_id = self.binder_for('odooconnector.sale.order').to_backend(
            record.order_id.id,
            wrap=True
        )
        if order_id:
            return {'order_id': order_id}

    @mapping
    def product_id(self, record):
        product_id = self.binder_for('odooconnector.product.product').\
            to_backend(record.product_id.id,
                       wrap=True
                       )
        if product_id:
            return {'product_id': product_id}

    @mapping
    def product_uom(self, record):
        product_uom = self.binder_for('odooconnector.product.uom').to_backend(
            record.product_uom.id,
            wrap=True
        )
        if not product_uom:
            raise MappingError('The UoM has no binding for this backend')
        _logger.debug('Using Product UoM %s for %s and line %s',
                      product_uom, record.product_uom, record.id)
        return {'product_uom': product_uom}

    @mapping
    def tax_id(self, record):
        if not record.tax_id:
            return
        tax_ids = []
        binder = self.binder_for('odooconnector.account.tax')
        for each_tax in record.tax_id:
            tax_id = binder.to_backend(each_tax.id, wrap=True)
            if tax_id:
                tax_ids.append(tax_id)
        return {'tax_id': [(6, 0, tax_ids)]}
