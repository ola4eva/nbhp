from odoo import api, fields, models


class Inheritcompany(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    warehouse_id = fields.Many2one('stock.warehouse',"Warehouse")
    source_location=fields.Many2one('stock.location',"Source Location")
    transit_location=fields.Many2one('stock.location',"Transit Location")
    stock_picking_type=fields.Many2one('stock.picking.type',"Stock Picking Type")
