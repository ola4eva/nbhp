from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError

<<<<<<< HEAD
class StockLocation(models.Model):
=======
class NewModule(models.Model):
>>>>>>> 54bb087fb778e077d0492339d4e0ed5781ca0702
    _name = 'stock.location'
    _inherit = 'stock.location'
    stock_user_id = fields.Many2one('res.users',"Stock User")
