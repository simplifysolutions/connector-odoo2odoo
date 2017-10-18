# -*- coding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

from openerp import models, fields

class ConnectorCheckpoint(models.Model):
    _inherit = 'connector.checkpoint'

    model_id = fields.Many2one(comodel_name='ir.model',
                               string='Model',
                               required=True,
                               readonly=True,
                               ondelete='cascade')