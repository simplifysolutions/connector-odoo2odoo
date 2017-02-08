# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

from openerp import models, fields
from openerp.addons.connector.unit.mapper import (
    ExportMapper, ImportMapper, mapping)
from openerp.addons.odooconnector_base.backend import oc_odoo, oc_odoo1000

from openerp.addons.odooconnector_base.models.partner import (
    PartnerExportMapper, PartnerImportMapper)


@oc_odoo1000
class PartnerImportMapperSalesTeam(PartnerImportMapper):
    _model_name = 'odooconnector.res.partner'

    @mapping
    def team_id(self, record):
        print"team_idteam_idteam_id"
        if not record.get('team_id'):
            return
        binder = self.binder_for('odooconnector.crm.case.section')
        team_id = binder.to_openerp(record['team_id'][0], unwrap=True)
        if team_id:
            return {'section_id': team_id}


@oc_odoo1000
class PartnerExportMapperSalesTeam(PartnerExportMapper):
    _model_name = 'odooconnector.res.partner'

    @mapping
    def team_id(self, record):
        if not record.section_id:
            return
        binder = self.binder_for('odooconnector.crm.case.section')
        team_id = binder.to_backend(record.section_id.id, wrap=True)
        if team_id:
            return {'team_id': team_id}
