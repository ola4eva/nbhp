from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError

class NewModule(models.Model):
    _name = 'stock.location'
    _inherit = 'stock.location'
    stock_user_id = fields.Many2one('res.users',"Stock User")
