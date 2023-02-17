# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_confirm(self):
        self.check_bom()
        return super().action_confirm()

    def check_bom(self):
        for rec in self:
            if not rec.bom_id.state == 'confirmed':
                raise UserError(_("BOM hasn't been confirmed, please confirm BOM before proceeding."))

