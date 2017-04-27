# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

from openerp import models, api


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def onchange_template_id(
            self, template_id, composition_mode, model, res_id):
        res = super(MailComposeMessage, self).onchange_template_id(
            template_id, composition_mode, model, res_id)
        if res.get('value', {}):
            res['value'].update({
                'composition_mode': composition_mode,
                'model': model,
                'res_id': res_id,
                'template_id': template_id,
            })
        return res
