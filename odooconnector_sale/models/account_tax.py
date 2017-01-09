from openerp import models, fields,api
from openerp.addons.odooconnector_base.backend import oc_odoo
from openerp.addons.odooconnector_base.unit.import_synchronizer import (OdooImporter,
                                        DirectBatchImporter)
from openerp.addons.odooconnector_base.unit.mapper import (
    OdooExportMapChild,OdooImportMapChild,OdooImportMapper)


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
class AccountTaxLineImporter(OdooImporter):
    _model_name = ['odooconnector.account.tax']

@oc_odoo
class AccountTaxLineImporterMapper(OdooImportMapper):
    _model_name = 'odooconnector.account.tax'

    _direct=[
        ('name', 'name'), ('code', 'code'),('type','type')
    ]
