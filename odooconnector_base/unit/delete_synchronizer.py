# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

import logging
from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Deleter
from ..connector import get_environment
_logger = logging.getLogger(__name__)


class OdooDeleter(Deleter):
    """ Base deleter for odoo """

    def _get_remote_model(self):
        """ Use this method to explicitly define a model which shall be called
        in the remote system """
        return

    def run(self, external_openerp_id):
        """ Run the synchronization, delete the record on Odoo

        :param external_openerp_id: identifier of the record to delete
        """
        remote_model = self._get_remote_model()
        self.backend_adapter.delete(external_openerp_id,model_name=remote_model)
        return _('Record %s deleted on external system') % external_openerp_id


OdooDeleteSynchronizer = OdooDeleter  # deprecated


@job(default_channel='root.odooconnector')
def export_delete_record(session, model_name, backend_id, external_openerp_id,api=None):
    """ Delete a record on Odoo """
    _logger.debug('Delete record for "%s"', model_name)
    env = get_environment(session, model_name, backend_id, api=api)
    deleter = env.get_connector_unit(OdooDeleter)
    return deleter.run(external_openerp_id)
