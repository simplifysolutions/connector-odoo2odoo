# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

from openerp import models, fields, api


class OdooBackend(models.Model):

    _inherit = 'odooconnector.backend'

    default_export_ir_attachment = fields.Boolean(
        string='Default Attachments export backend',
        help='Use this backend as default for the SO process.'
    )
    default_export_ir_attachment_domain = fields.Char(
        string='Export Attachments Domain',
        default='[]'
    )

    @api.multi
    def export_attachements(self):
        """ Export attachements to external system """
        self._export_records('ir.attachment')
        return True
