# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp.addons.connector.connector import Binder
from openerp.addons.connector.event import on_record_write, on_record_create,on_record_unlink

from .unit.export_synchronizer import export_record
from .unit.delete_synchronizer import export_delete_record
from .connector import get_environment


_logger = logging.getLogger(__name__)

# Some patching of the original write / create events:
# This is a security mechanism to prevent cyclic export processes
original_fire_create = on_record_create.fire
original_fire_write = on_record_write.fire
original_fire_unlink = on_record_unlink.fire


# TODO(MJ): Patching should be done on install, not on import!
def new_fire(original):
    def new_fire(self, session, model_name, *args, **kwargs):
        config_obj = self.env['ir.config_parameter']
        export = config_obj.get_param('odooconnector.export_sync') or None
        # TODO(MJ): Must be changed!
        if export and eval(export):
            original(self, session, model_name, *args, **kwargs)
        else:
            _logger.debug('Did not fire "%s"' % original)
    return new_fire


on_record_create.fire = new_fire(original_fire_create)
on_record_write.fire = new_fire(original_fire_write)
on_record_unlink.fire = new_fire(original_fire_unlink)


@on_record_create(model_names=['odooconnector.product.product',
                               'odooconnector.product.uom',
                               'odooconnector.res.partner',
                               'odooconnector.res.users',
                               'odooconnector.product.pricelist',
                               'odooconnector.product.pricelist.item',
                               ])
def export_odooconnector_object(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return

    _logger.debug('Record creation triggered for "%s(%s)"',
                  model_name, record_id)
    sync_object(session, model_name, record_id, fields)


@on_record_create(model_names=['product.product',
                               'res.users',
                               'res.partner',
                               'product.pricelist',
                               'product.pricelist.item',
                               'product.uom',
                               ])
def create_default_binding(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    _logger.debug('Record creation triggered for "%s(%s)"',
                  model_name, record_id)

    obj = session.env[model_name].browse(record_id)

    default_backends = session.env['odooconnector.backend'].search(
        [('default_export_backend', '=', True)]
    )
    ic_model_name = 'odooconnector.' + model_name
    for backend in default_backends:
        _logger.debug('Create binding for default backend %s', backend.name)
        session.env[ic_model_name].create({
            'backend_id': backend.id,
            'openerp_id': obj.id,
            'exported_record': True
        })


# TODO(MJ): At this time, if product.template and product.product fields get
#           changed in the same transaction (e.g. in the product view), two
#           export jobs will be created: one for product.template and one for
#           product.product. If you have more than one export backend, this
#           gets even multiplied by the amount of backends: 2 backends means
#           4 export jobs. So far I have no idea how to deal with this!
@on_record_write(model_names=['product.product', 'product.template'])
def update_product(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    _logger.debug('Record write triggered for %s(%s)', model_name, record_id)

    # In the procedure of creating a new product.template this check prevents
    # creating redundant export jobs
    if not fields:
        _logger.debug('Sync skipped for "%s(%s) [No fields]"',
                      model_name, record_id)
        return
    else:
        ic_model_name = 'odooconnector.product.product'
        bindings = []

        if model_name == 'product.template':
            fields = {}  # product.template fields are not compatible with p.p
            obj = session.env['product.template'].browse(record_id)
            for product in obj.product_variant_ids:
                for binding in product.oc_bind_ids:
                    bindings.append(binding)

        else:
            model_name = 'odooconnector.product.product'
            obj = session.env['product.product'].browse(record_id)
            bindings = obj.oc_bind_ids

        for binding in bindings:
            _logger.debug('Sync process start for "%s(%s)"',
                          model_name, binding.id)
            sync_object(session, ic_model_name, binding.id, fields)


@on_record_write(model_names=['res.partner',
                              'res.users',
                              'product.uom',
                              'product.pricelist',
                              'product.pricelist.item'])
def update_records(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    _logger.debug('Record write triggered for %s(%s)', model_name, record_id)

    # In the procedure of creating a new product.template this check prevents
    # creating redundant export jobs
    if not fields:
        _logger.debug('Sync skipped for "%s(%s) [No fields]"',
                      model_name, record_id)
        return
    else:
        ic_model_name = 'odooconnector.' + model_name
        obj = session.env[model_name].browse(record_id)

        for binding in obj.oc_bind_ids:
            _logger.debug('Sync process start for "%s(%s)"',
                          model_name, binding.id)
            sync_object(session, ic_model_name, binding.id, fields)

@on_record_unlink(model_names=['product.product', 'product.template'])
def unlink_product_data(session, model_name, record_id):
    if session.context.get('connector_no_export'):
        return
    _logger.debug('Record write triggered for %s(%s)', model_name, record_id)
    ic_model_name = 'odooconnector.product.product'
    bindings = []
    if model_name == 'product.template':
        obj = session.env['product.template'].browse(record_id)
        for product in obj.product_variant_ids:
            for binding in product.oc_bind_ids:
                bindings.append(binding)
    else:
        obj = session.env['product.product'].browse(record_id)
        bindings = obj.oc_bind_ids
    for binding in bindings:
        _logger.debug('Sync process start for "%s(%s)"',
                      model_name, binding.id)
        sync_unlink(session, ic_model_name, binding.id)

@on_record_unlink(model_names=['product.pricelist.item'])
def unlink_object_data(session, model_name, record_id):
    if session.context.get('connector_no_export'):
        return
    _logger.debug('Record write triggered for %s(%s)', model_name, record_id)

    ic_model_name = 'odooconnector.' + model_name
    obj = session.env[model_name].browse(record_id)
    for binding in obj.oc_bind_ids:
        _logger.debug('Sync process start for "%s(%s)"',
                      model_name, binding.id)
        sync_unlink(session, ic_model_name, binding.id)



def sync_object(session, model_name, record_id, fields=None):
    domain = []
    if session.context.get('connector_no_export'):
        return
    if session.context.get('domain'):
        domain = session.context.get('domain')
    obj = session.env[model_name].search(domain + [('id', '=', record_id)])
    if obj:
        _logger.debug('Sync record')
        export_record.delay(session, model_name, obj.backend_id.id, record_id)
    else:
        _logger.debug('Sync skipped for %s(%s) [No binding]',
                      model_name, record_id)


def sync_unlink(session, model_name, record_id):
    """ Sync job which delete a record on external system.

    Called on binding records."""
    domain = []
    if session.context.get('connector_no_export'):
        return
    if session.context.get('domain'):
        domain = session.context.get('domain')
    obj = session.env[model_name].search(domain + [('id', '=', record_id)])
    if obj:
        _logger.debug('Sync record')
        env = get_environment(session, model_name, obj.backend_id.id)
        binder = env.get_connector_unit(Binder)
        external_openerp_id = binder.to_backend(record_id)
        if external_openerp_id:
            export_delete_record.delay(session, model_name,
                                   obj.backend_id.id, external_openerp_id)