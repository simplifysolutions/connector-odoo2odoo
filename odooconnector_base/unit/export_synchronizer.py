# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import time
import logging

from openerp.tools.safe_eval import safe_eval
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Exporter
from openerp.addons.connector.exception import InvalidDataError
from openerp.addons.connector.connector import ConnectorUnit
from ..backend import oc_odoo

from ..connector import get_environment, add_checkpoint


_logger = logging.getLogger(__name__)


class OdooExporter(Exporter):

    def __init__(self, connector_env):
        super(OdooExporter, self).__init__(connector_env)
        self.binding_id = None

    def _pre_export_check(self, record):
        """ Check if the record is allowed to be exported."""
        return True

    def _pre_export_domain_check(self, record, domain):
        """ Convinience method to check if a record matches a given domain

        :param record: Odoo record
        :param domain: domain expression, e.g. [('id', '>', '10')]
        """
        # TODO(MJ): Replace this eval expression!
        results = self.env[self._get_remote_model()].search(
                safe_eval(domain))
        if record.openerp_id.id in results.ids:
            return True
        return False

    def _get_remote_model(self):
        """ Use this method to explicitly define a model which shall be called
        in the remote system """
        return

    def _after_export(self, record_created=False):
        """ Hook called at the end of the export

        Use this hook for executing arbitrary actions, e.g. export translations
        :param record_created: indicates whether the record was created
        """
        return

    def _export_dependency(self, relation, binding_model, exporter_class=None,
                           binding_field='oc_bind_ids',
                           binding_extra_vals=None):
        """
        Export a dependency. The exporter class is a subclass of
        ``OdooExporter``. If a more precise class need to be defined,
        it can be passed to the ``exporter_class`` keyword argument.

        .. warning:: a commit is done at the end of the export of each
                     dependency. The reason for that is that we pushed a record
                     on the backend and we absolutely have to keep its ID.

                     So you *must* take care not to modify the OpenERP
                     database during an export, excepted when writing
                     back the external ID or eventually to store
                     external data that we have to keep on this side.

                     You should call this method only at the beginning
                     of the exporter synchronization,
                     in :meth:`~._export_dependencies`.

        :param relation: record to export if not already exported
        :type relation: :py:class:`openerp.models.BaseModel`
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param exporter_cls: :py:class:`openerp.addons.connector\
                                        .connector.ConnectorUnit`
                             class or parent class to use for the export.
                             By default: OdooExporter
        :type exporter_cls: :py:class:`openerp.addons.connector\
                                       .connector.MetaConnectorUnit`
        :param binding_field: name of the one2many field on a normal
                              record that points to the binding record
                              (default: oc_bind_ids).
                              It is used only when the relation is not
                              a binding but is a normal record.
        :type binding_field: str | unicode
        :binding_extra_vals:  In case we want to create a new binding
                              pass extra values for this binding
        :type binding_extra_vals: dict
        """
        if not relation:
            return
        if exporter_class is None:
            exporter_class = OdooExporter
        rel_binder = self.binder_for(binding_model)
        # wrap is typically True if the relation is for instance a
        # 'product.product' record but the binding model is
        # 'odooconnector.product.product'
        wrap = relation._model._name != binding_model

        if wrap and hasattr(relation, binding_field):
            domain = [('openerp_id', '=', relation.id),
                      ('backend_id', '=', self.backend_record.id)]
            binding = self.env[binding_model].search(domain)
            if binding:
                assert len(binding._ids) == 1, (
                    'only 1 binding for a backend is '
                    'supported in _export_dependency')
            # we are working with a unwrapped record (e.g.
            # product.category) and the binding does not exist yet.
            # Example: I created a product.product and its binding
            # odooconnector.product.product and we are exporting it, but we need to
            # create the binding for the product.category on which it
            # depends.
            else:
                bind_values = {'backend_id': self.backend_record.id,
                               'openerp_id': relation.id}
                if binding_extra_vals:
                    bind_values.update(binding_extra_vals)
                # If 2 jobs create it at the same time, retry
                # one later. A unique constraint (backend_id,
                # openerp_id) should exist on the binding model
                with self._retry_unique_violation():
                    binding = (self.env[binding_model]
                               .with_context(connector_no_export=True)
                               .sudo()
                               .create(bind_values))
                    # Eager commit to avoid having 2 jobs
                    # exporting at the same time. The constraint
                    # will pop if an other job already created
                    # the same binding. It will be caught and
                    # raise a RetryableJobError.
                    self.session.commit()
        else:
            # If oc_bind_ids does not exist we are typically in a
            # "direct" binding (the binding record is the same record).
            # If wrap is True, relation is already a binding record.
            binding = relation

        if not rel_binder.to_backend(binding.openerp_id):
            exporter = self.unit_for(exporter_class, model=binding_model)
            exporter.run(binding.id)

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        return

    def run(self, binding_id):
        """ Run the export synchronization

        :param binding_id: identifier for the binding record
        """
        time_start = time.time()
        self.binding_id = binding_id

        record = self.model.browse(binding_id)

        if not self._pre_export_check(record):
            _logger.info('Record did not pass pre-export check.')
            return "Pre-Export check was not successfull"

        self._export_dependencies()

        mapped_record = self.mapper.map_record(record)

        remote_model = self._get_remote_model()
        external_id = self.binder.to_backend(self.binding_id)
        record_created = False

        # Create a new record or update the existing record
        if external_id:
            _logger.debug('Found binding %s', external_id)
            data = mapped_record.values()
            result = self.backend_adapter.write(
                external_id, data, model_name=remote_model
            )
            if not result:
                # Note: When using @on_record_create / _write events, raising
                #       an exception can lead to inconsistent data.
                #       Example: create product supplierinfo for an supplier
                #       thats is not available in the ic backend.
                # raise InvalidDataError("Something went wrong while writing.")
                return 'Could not export'
        else:
            _logger.debug('No binding found, creating a new record')
            data = mapped_record.values(for_create=True)
            external_id = self.backend_adapter.create(
                data, model_name=remote_model
            )

            if not external_id:
                raise InvalidDataError("Something went wrong while creating.")

            record_created = True

        self.binder.bind(external_id, self.binding_id, exported=True)
        self.external_id = external_id
        self.session.commit()
        self._after_export(record_created=record_created)

        time_end = time.time()
        _logger.warning("Finished exporting record (%s, %s)[%s]",
                        binding_id, external_id, time_end - time_start)


class TranslationExporter(Exporter):
    """ Exporter for translation enabled fields """

    def _get_record(self, language):
        """Get the to be exported recorded in the defined language """
        context = {'lang': language}
        return self.model.with_context(**context).browse(self.binding_id)

    def _get_languages(self):
        """ Hook method for languages to export

        :returns: language codes
        :rtype: list
        """
        term = [('translatable', '=', True)]
        langs = self.env['res.lang'].search(term)
        return [l.code for l in langs]

    def _get_translatable_fields(self):
        """ Get the names of the fields that can be translated

        :returns: list of translatable fields
        :rtype: list
        """
        model_fields = self.model.fields_get()
        trans_fields = [field for field, attrs in model_fields.iteritems()
                        if attrs.get('translate')]
        _logger.debug('Translatable fields: %s', trans_fields)
        return trans_fields

    def run(self, external_id, binding_id, mapper_class=None):
        _logger.debug('Running translation exporter...')
        self.external_id = external_id
        self.binding_id = binding_id

        if mapper_class:
            mapper = self.unit_for(mapper_class)
        else:
            mapper = self.mapper

        trans_fields = self._get_translatable_fields()
        binding = self.model.browse(binding_id)

        if not binding:
            _logger.debug('No binding found for %s, skip translation export',
                          binding_id)
            return

        for language in self._get_languages():
            _logger.debug('Process language %s', language)
            record = self._get_record(language)
            mapped_record = mapper.map_record(record)
            record_values = mapped_record.values()

            # TODO(MJ): As long as we use explicit translation mapper per
            #           model, this logic is actually not necessary.
            #           If we move to a more generic translation mapper, we
            #           might use this logic!
            data = {field: value for field, value in record_values.iteritems()
                    if field in trans_fields}

            _logger.debug('Record values: %s', record_values)
            self.backend_adapter.write(
                external_id, data, context={'lang': language}
            )

class BatchExporter(Exporter):
    """ Search for a list of items to export. Export them directly or delay
    the export of each item (see DirectBatchExporter, DelayedBatchExporter)
    """

    def run(self, filters=None):
        """ Run the synchronization """
        _logger.debug("BatchExporter started")
        #FIXME: Clunky and ugh with the eval
        record_ids = self.env[self._get_remote_model()].search(
            safe_eval(filters))

        for record_id in record_ids:
            self._export_record(record_id, api=self.connector_env.api)

    def _export_record(self, record_id, api=None):
        """ Export the record directly or delay it.

        Method must be implemented in sub-classes.
        """
        raise NotImplementedError

class DirectBatchExporter(BatchExporter):
    """ Export the records directly. Do not delay export to jobs. """

    _model_name = None

    def _export_record(self, record_id, api=None):
        """ Export record directly """
        export_record(self.session, self.model._name, self.backend_record.id,
                      record_id, api=api)

@oc_odoo
class AddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the underlying model
    (not the odooconnector.* but the _inherits'ed model) """

    _model_name = ['odooconnector.product.pricelist.item',
                   'odooconnector.product.pricelist',
                ]
    
    def run(self, openerp_binding_id):
        binding = self.model.browse(openerp_binding_id)
        record = binding.openerp_id
        add_checkpoint(self.session,
                       record._model._name,
                       record.id,
                       self.backend_record.id)


@job
def export_batch(session, model_name, backend_id, filters=None):
    """ Prepare a batch export of records """
    _logger.debug("Export batch for '{}'".format(model_name))
    env = get_environment(session, model_name, backend_id)
    exporter = env.get_connector_unit(BatchExporter)
    exporter.run(filters=filters)

@job(default_channel='root.odooconnector')
def export_record(session, model_name, backend_id, binding_id,
                  fields=None, api=None):
    _logger.debug('Export record for "%s"', model_name)
    env = get_environment(session, model_name, backend_id, api=api)

    #TODO: LANGUAGE STUFF
    exporter = env.get_connector_unit(OdooExporter)
    exporter.run(binding_id)
