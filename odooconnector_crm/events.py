# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

import logging
from openerp.addons.odooconnector_base import events


_logger = logging.getLogger(__name__)


@events.on_record_create(model_names=['odooconnector.crm.lead',
                                      ])
def export_odooconnector_object(session, model_name, record_id, fields=None):
    return events.export_odooconnector_object(
        session, model_name, record_id, fields=fields)


@events.on_record_create(model_names=['crm.lead'])
def create_default_binding(session, model_name, record_id, fields=None):
    return events.create_default_binding(
        session, model_name, record_id, fields=fields)


@events.on_record_write(model_names=['crm.lead'])
def update_crm_leads(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    _logger.debug('Record write triggered for %s(%s)', model_name, record_id)

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
            events.sync_object(session, ic_model_name, binding.id, fields)
