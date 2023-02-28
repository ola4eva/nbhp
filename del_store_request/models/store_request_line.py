# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api

# class IRRequestLine(models.Model):
#     _name = 'ng.ir.request.line'
#
#     request_id = fields.Many2one(comodel_name='ng.ir.request', string='Request')
#     product_id = fields.Char(string='Product')
#     quantity = fields.Float(string='Quantity', default=1.0)
#     uom = fields.Many2one(comodel_name='product.uom', string='U.O.M')


class LineApprove(models.Model):
    _name = 'store.request.approve'

    @api.onchange('product_id')
    def onchangeproduct(self):
        for con in self:
            if con.product_id:
                con.uom=con.product_id.uom_id

    REQUEST_STAGE = [
        ('draft', 'Draft'),
        ('submit', 'Department Manager'),
        ('approved', 'Centra Warehouse Manager Approval'),
        ('warehouse', 'Warehouse Officer'),
        ('approval', 'Warehouse Manager'),
        ('transfer', 'Transfer'),
        ('done', 'Done'),
        ('receive', 'Received')
    ]


    STATE = [
        ('not_available', 'Not Available'),
        ('partially_available', 'Partially Available'),
        ('available', 'Available'),
        ('awaiting', 'Awaiting Availability'),
    ]
    state_main = fields.Selection(selection=REQUEST_STAGE, track_visibility='onchange',related='request_id.state', default ='draft')
    request_id = fields.Many2one('store.request', string='Request')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity', default=1.0,readonly=False)
    uom = fields.Many2one('uom.uom', string='U.O.M')
    qty = fields.Float(string='Qty Available', compute='_compute_qty')
    received_qty = fields.Float(string='Qty Received')
    state = fields.Selection(selection=STATE, string='State', compute='_compute_state', store=False)
    purchase_agreement = fields.Char(string='Purchase Agreement')
    to_procure = fields.Boolean(string='To Procure', compute='_compute_to_procure')
    transferred = fields.Boolean(string='Transferred', default=False)

    @api.depends('state')
    # @api.one
    def _compute_to_procure(self):
        for con in self:
            to_procure = (con.state == 'partially_available' or con.state == 'not_available')
            if con.purchase_agreement:
                con.to_procure = False
            else:
                con.to_procure = to_procure

    @api.depends('product_id')
    # @api.one
    def _compute_qty(self):
        for con in self:
            location_id = con.request_id.src_location_id.id
            product_id = con.product_id.id
            stock_quants = con.env['stock.quant'].search([('location_id', '=', location_id), ('product_id', '=', product_id)])
            con.qty = sum([stock_quant.available_quantity for stock_quant  in stock_quants])

    @api.depends('qty')
    # @api.one
    def _compute_state(self):
        for con in self:
            if con.qty <= 0:
                con.state = 'not_available'
            elif con.qty > 0 and con.qty < con.quantity:
                con.state ='partially_available'
            else:
                con.state = 'available'

    # @api.multi
    def procure(self):
        product_id, quantity =  self.product_id, self.quantity - self.qty
        requisition = self.env['purchase.requisition']
        line = self.env['purchase.requisition.line']
        request_identity = self.request_id.name
        requisition_id = requisition.create({'origin':self.request_id.name})
        payload = {
            'product_id':product_id.id,
            'product_uom_id':product_id.uom_id.id,
            'product_qty': quantity,
            'qty_ordered': quantity,
            'requisition_id':requisition_id.id,
            'price_unit': product_id.standard_price
        }
        line.create(payload)
        self.purchase_agreement = requisition_id.name
        # Rename the purchase requestion name to ref
        origin = '{}/{}'.format(request_identity, requisition_id.name)
        requisition_id.write({'name':origin})

