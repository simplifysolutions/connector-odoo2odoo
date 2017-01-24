# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

from openerp.addons.odooconnector_base.backend import oc_odoo
from openerp.addons.odooconnector_base.unit.backend_adapter import OdooAdapter


@oc_odoo
class OdooAdapterSale(OdooAdapter):
    _model_name = [
        'odooconnector.sale.order',
        'odooconnector.sale.order.line',
        'odooconnector.account.tax',
    ]
