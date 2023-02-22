# -*- coding: utf-8 -*-

from odoo import models, fields, _



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    attachment = fields.Binary('Attachment', attachment=True)
    attachment_name = fields.Char('Attachment Name')