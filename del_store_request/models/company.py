from odoo import api, fields, models


<<<<<<< HEAD
class ResCompany(models.Model):
=======
class Inheritcompany(models.Model):
>>>>>>> 54bb087fb778e077d0492339d4e0ed5781ca0702
    _name = 'res.company'
    _inherit = 'res.company'

    warehouse_id = fields.Many2one('stock.warehouse',"Warehouse")
    source_location=fields.Many2one('stock.location',"Source Location")
    transit_location=fields.Many2one('stock.location',"Transit Location")
    stock_picking_type=fields.Many2one('stock.picking.type',"Stock Picking Type")
