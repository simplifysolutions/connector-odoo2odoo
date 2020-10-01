# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector.exception import MappingError
from odoo.addons.queue_job.exception import NothingToDoJob

_logger = logging.getLogger(__name__)


class ProductCategoryBatchImporter(Component):
    """ Import the Odoo Product Categories.

    For every product category in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level categories imported first.
    """

    _name = "odoo.product.category.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.product.category"]

    def _import_record(self, external_id, job_options=None):
        """ Delay a job for the import """
        super(ProductCategoryBatchImporter, self)._import_record(
            external_id, job_options=job_options
        )

    def run(self, filters=None):
        """ Run the synchronization """

        updated_ids = self.backend_adapter.search(filters)

        base_priority = 10
        for cat in updated_ids:
            cat_id = self.backend_adapter.read(cat)
            job_options = {"priority": base_priority + cat_id.parent_left or 0}
            self._import_record(cat_id.id, job_options=job_options)


class ProductCategoryImporter(Component):
    _name = "odoo.product.category.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.product.category"]

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.odoo_record
        # import parent category
        # the root category has a 0 parent_id
        if record.parent_id:
            self._import_dependency(record.parent_id.id, self.model)

    def _import_dependency(
        self, external_id, binding_model, importer=None, always=False
    ):
        """ Import a dependency.

        The importer class is a class or subclass of
        :class:`OdooImporter`. A specific class can be defined.

        :param external_id: id of the related binding to import
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param importer_component: component to use for import
                                   By default: 'importer'
        :type importer_component: Component
        :param always: if True, the record is updated even if it already
                       exists, note that it is still skipped if it has
                       not been modified on Odoo since the last
                       update. When False, it will import it only when
                       it does not yet exist.
        :type always: boolean
        """
        if not external_id:
            return
        binder = self.binder_for(binding_model)
        if always or not binder.to_internal(external_id, unwrap=True):
            if importer is None:
                importer = self.component(
                    usage="record.importer", model_name=binding_model
                )
            try:
                importer.run(external_id)
            except NothingToDoJob:
                _logger.info(
                    "Dependency import of %s(%s) has been ignored.",
                    binding_model._name,
                    external_id,
                )

    def _after_import(self, binding):
        """ Hook called at the end of the import """


#         translation_importer = self.component(usage='translation.importer')
#         translation_importer.run(self.external_id, binding)


class ProductCategoryImportMapper(Component):
    _name = "odoo.product.category.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.product.category"

    direct = [("name", "name"), ("type", "type")]

    @only_create
    @mapping
    def odoo_id(self, record):
        # TODO: Improve the matching on name and position in the tree so that
        # multiple categ with the same name will be allowed and not duplicated
        categ_id = self.env["product.category"].search(
            [("name", "=", record.name)]
        )
        _logger.debug(
            "found category {} for record {}".format(categ_id, record)
        )
        if len(categ_id) == 1:
            return {"odoo_id": categ_id.id}
        return {}

    @mapping
    def parent_id(self, record):
        if not record.parent_id:
            return
        binder = self.binder_for()
        parent_binding = binder.to_internal(record.parent_id.id)

        if not parent_binding:
            raise MappingError(
                "The product category with "
                "Odoo id %s is not imported." % record.parent_id.id
            )

        parent = parent_binding.odoo_id
        return {"parent_id": parent.id, "odoo_parent_id": parent_binding.id}
