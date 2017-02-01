# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
try:
    import odoorpc
except ImportError:
    pass
from openerp.addons.connector.connector import ConnectorEnvironment
from openerp.addons.connector.checkpoint import checkpoint

_logger = logging.getLogger(__name__)


class APIConnectorEnvironment(ConnectorEnvironment):
    """ Custom connector environment for wrapping a Odoo api in it.

    NOTE: Storing the Odoo API instance should result in a better performance
    """

    _propagate_kwargs = ['api']

    def __init__(self, backend_record, session, model_name, api=None):
        super(APIConnectorEnvironment, self).__init__(
            backend_record, session, model_name)
        self.api = api


def get_odoo_api(hostname, port, database, protocol, username, password):
    """ Create a OERP instance for further reuse """
    # TODO(MJ): Switch to OdooRPC and test performance in load test
    api = odoorpc.ODOO(hostname, port=port, protocol=protocol)

    api.login(database, username, password)

    _logger.info('Created a new Odoo API instance')
    return api
    # return api.env.user


def get_environment(session, model_name, backend_id, api=None):
    """ Create a custom environment to work with """
    backend_record = session.env['odooconnector.backend'].browse(backend_id)

    if not api:
        protocol = 'jsonrpc'
        if backend_record.ssl:
            protocol = 'jsonrpc+ssl'
        api = get_odoo_api(backend_record.hostname, backend_record.port,
                           backend_record.database, protocol,
                           backend_record.username, backend_record.password)

    env = APIConnectorEnvironment(backend_record, session, model_name, api=api)
    lang = backend_record.default_lang_id
    lang_code = lang.code if lang else 'en_US'
    if lang_code == session.context.get('lang'):
        return env
    else:
        with env.session.change_context(lang=lang_code):
            return env


def add_checkpoint(session, model_name, record_id, backend_id):
    """ Add a row in the model ``connector.checkpoint`` for a record,
    meaning it has to be reviewed by a user.

    :param session: current session
    :type session: :class:`openerp.addons.connector.session.ConnectorSession`
    :param model_name: name of the model of the record to be reviewed
    :type model_name: str
    :param record_id: ID of the record to be reviewed
    :type record_id: int
    :param backend_id: ID of the Odoo Backend
    :type backend_id: int
    """
    return checkpoint.add_checkpoint(session, model_name, record_id,
                                     'odooconnector.backend', backend_id)
