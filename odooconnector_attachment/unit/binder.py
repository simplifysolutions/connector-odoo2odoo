# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

from openerp.addons.odooconnector_base.unit.binder import OdooModelBinder
from openerp.addons.odooconnector_base.backend import oc_odoo


@oc_odoo
class OdooModelBinderAttachment(OdooModelBinder):
    _model_name = [
        'odooconnector.ir.attachment',
    ]
