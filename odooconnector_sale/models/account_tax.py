from openerp import models, fields,api
from openerp.addons.connector.unit.mapper import (ExportMapper,ImportMapper, mapping)
from openerp.addons.odooconnector_base.backend import oc_odoo
from openerp.addons.odooconnector_base.unit.import_synchronizer import (OdooImporter,
                                        DirectBatchImporter)
from openerp.addons.odooconnector_base.unit.mapper import (
    OdooExportMapChild,OdooImportMapChild,OdooImportMapper)
from openerp.addons.odooconnector_base.unit.export_synchronizer import (
    OdooExporter)


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
class AccountTaxImporter(OdooImporter):
    _model_name = ['odooconnector.account.tax']

@oc_odoo
class AccountTaxImporterMapper(OdooImportMapper):
    _model_name = ['odooconnector.account.tax']

    direct=[
        ('name', 'name'), ('description', 'description'),('type','type'),
        ('amount','amount'),
    ]

#@oc_odoo
#class AccountTaxBatchExporter(DirectBatchExporter):
#    _model_name = ['odooconnector.account.tax']

@oc_odoo
class AccountTaxExporter(OdooExporter):
    _model_name = ['odooconnector.account.tax']

    def _get_remote_model(self):
        return 'account.tax'

    def _after_export(self, record_created):
        # create a ic_binding in the backend, indicating that the partner
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
                model_name='odooconnector.account.tax',
                context={'connector_no_export': True}
            )


@oc_odoo
class AccountTaxExporterMapper(ExportMapper):
    _model_name = ['odooconnector.account.tax']

    direct=[
        ('name', 'name'), ('description', 'description'),('type','type'),
        ('amount','amount')
    ]
