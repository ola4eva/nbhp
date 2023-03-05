# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class StoreRequest(models.Model):
    _name = 'store.request'
    _inherit = ['mail.thread']
    _description = "Material Requisition"
    _order = 'create_date desc, state desc, write_date desc'

    def _current_login_user(self):
        """Return current logined in user."""
        return self.env.uid

    REQUEST_STAGE = [
        ('draft', 'Draft'),
        ('submit', 'Department Manager'),
        ('approved', 'Warehouse Officer'),
        ('transfer', 'Transfer'),
        ('done', 'Done'),
        ('receive', 'Received'),
        ('reject', 'Rejected'),
    ]

    def _current_login_employee(self):
        """Get the employee record related to the current login user."""
        hr_employee = self.env['hr.employee'].sudo().search(
            [('user_id', '=', self.env.user.id)])
        return hr_employee and hr_employee.id

    @api.onchange('end_user')
    def get_hod_from_end_user(self):
        if self.end_user:
            self.hod = self.end_user.department_id.manager_id.id

    name = fields.Char(string='Number', default='/', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(selection=REQUEST_STAGE,
                             default='draft', tracking=True)
    requester = fields.Many2one('res.users', string='Requester', default=_current_login_user,
                                tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    end_user = fields.Many2one(
        'hr.employee', string='End User', required=True, 
        default=_current_login_employee
        )
    request_date = fields.Datetime(string='Request Date', default=lambda self: datetime.now(),
                                   help='The day in which request was initiated')
    request_deadline = fields.Datetime(string='Request Deadline')
    hod = fields.Many2one('hr.employee', string='H.O.D', store=True)
    department = fields.Many2one(
        'hr.department', 
        related='end_user.department_id', 
        string='Department')
    dst_location_id = fields.Many2one('stock.location', string='Destination Location',
                                      help='Departmental Stock Location', tracking=True, required=False,
                                      domain=[('usage', '!=', 'view')])
    src_location_id = fields.Many2one('stock.location', string='Source Location',
                                      help='Departmental Stock Location', tracking=True, default=lambda self: self.env.user.company_id.source_location if (self.internal_request == True) else None)
    internal_request = fields.Boolean("Internal  Request")

    approve_request_ids = fields.One2many(
        'store.request.approve', 'request_id', string='Request Line', required=True, readonly=True, states={'draft': [('readonly', False)]})
    reason = fields.Text(string='Rejection Reason')
    availability = fields.Boolean(
        string='availability', compute='_compute_availabilty')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   default=lambda self: self.env.user.company_id.warehouse_id if (self.internal_request == True) else None)
    company_id = fields.Many2one(
        'res.company', string='Company', index=True, default=lambda self: self.env.company)

    transit_location_id = fields.Many2one('stock.location', string="Transit Location", domain=[('usage', '=', 'transit')],
                                          default=lambda self: self.env.user.company_id.transit_location)
    stock_picking_type = fields.Many2one(
        'stock.picking.type', string="Stock Picking Type", default=lambda self: self.env.user.company_id.stock_picking_type)

    @api.depends('approve_request_ids')
    def _compute_availabilty(self):
        count_total = len(self.approve_request_ids)
        count_avail = len(
            [appr_id.state for appr_id in self.approve_request_ids if appr_id.state == 'available'])
        self.availability = count_total == count_avail

    def submit(self):
        seq = self.env['ir.sequence'].next_by_code('store.request')
        recipient = self.recipient('hod', self.hod)
        url = self.request_link()
        mail_template = self.env.ref(
            'del_store_request.store_requisition_submit')
        mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(
            self.id, force_send=True)
        self.write({'state': 'submit', 'name': seq})

    def department_manager_approve(self):
        if self:
            url = self.request_link()
            recipient = self.recipient('department_manager', self.department)
            mail_template = self.env.ref(
                'del_store_request.store_requisition_approval')
            mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(
                self.id, force_send=True)
            self.write({'state': 'approved'})

    def main_manager_approve(self):
        self.write({'state': 'approval'})

    def warehouse_officer_confirm(self):
        if not self.approve_request_ids:
            raise UserError('Please add requested items.')
        else:
            url = self.request_link()
            recipient = self.recipient('department_manager', self.department)
            mail_template = self.env.ref(
                'del_store_request.store_requisition_warehouse_officer')
            mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(
                self.id, force_send=True)
            self.write({'state': 'transfer'})

    def warehouse_officer_confirm_qty(self):
        for con in self.approve_request_ids:
            if con.qty >= con.quantity:
                raise ValidationError("Requested Quantity Available")
            elif con.qty < con.quantity:
                raise ValidationError(
                    "Available Quantity not enough click to procure")

    def confirmation(self):
        if self.src_location_id.stock_user_id.id != self.env.uid:
            raise ValidationError("You are not the warehouse owner")

        self.write({'state': 'transfer'})

    def do_transfer_receive(self):
        for con in self.approve_request_ids:
            if not con.received_qty:
                raise ValidationError("Quantity received not entered")
        if self.requester.id != self.env.user.id:
            print(self.env.user.id, self.requester.id)
            raise ValidationError('You are not the Requester')
        if not self.dst_location_id:
            raise ValidationError("Pls select a Destination Location")
        if self:
            dst_location_id = self.dst_location_id.id
            transit_location_id = self.transit_location_id.id
            domain = [
                ('code', '=', 'internal'),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('active', '=', True)
            ]
            stock_picking = self.env['stock.picking']
            picking_type = self.env['stock.picking.type'].search(
                domain, limit=1)
            print(picking_type)
            payload = {
                'location_id': transit_location_id,
                'location_dest_id': dst_location_id,
                'picking_type_id': picking_type.id
            }
            stock_picking_id = stock_picking.create(payload)
            self.process(stock_picking_id)
            stock_picking_id.action_confirm()
            stock_picking_id.action_set_quantities_to_reservation()
            stock_picking_id.button_validate()

    def do_transfer(self):
        if not self.transit_location_id:
            raise ValidationError("Pls select a Transit Location")
        if self:
            src_location_id = self.src_location_id.id
            transit_location_id = self.transit_location_id.id
            domain = [
                ('code', '=', 'internal'),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('active', '=', True)
            ]
            stock_picking = self.env['stock.picking']
            picking_type = self.env['stock.picking.type'].search(
                domain, limit=1)
            print(picking_type)
            payload = {
                'location_id': src_location_id,
                'location_dest_id': transit_location_id,
                'picking_type_id': picking_type.id
            }
            stock_picking_id = stock_picking.create(payload)
            stock_picking_id.action_confirm()
            stock_picking_id.action_set_quantities_to_reservation()
            stock_picking_id.button_validate()

    def stock_move(self, request_ids, picking_id):
        """."""
        stock_move = self.env['stock.move']
        for request_id in request_ids:
            payload = {
                'product_id': request_id.product_id.id,
                'name': request_id.product_id.display_name,
                'product_uom_qty': request_id.quantity,
                'product_uom': request_id.uom.id,
                'picking_id': picking_id.id,
                'location_id': picking_id.location_id.id,
                'location_dest_id': picking_id.location_dest_id.id
            }
            stock_move.create(payload)
            request_id.write({'transferred': True})
        self.write({'state': 'done'})

    def stock_move_received(self, request_ids, picking_id):
        """."""
        stock_move = self.env['stock.move']
        for request_id in request_ids:
            payload = {
                'product_id': request_id.product_id.id,
                'name': request_id.product_id.display_name,
                'product_uom_qty': request_id.received_qty,
                'product_uom': request_id.uom.id,
                'picking_id': picking_id.id,
                'location_id': picking_id.location_id.id,
                'location_dest_id': picking_id.location_dest_id.id
            }
            stock_move.create(payload)
            request_id.write({'transferred': True})
        self.write({'state': 'receive'})

    def process(self, picking_id):
        if picking_id.state == 'draft':
            picking_id.action_confirm()
            if picking_id.state != 'assigned':
                picking_id.action_assign()
                if picking_id.state != 'assigned':
                    raise UserError(
                        ("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
        picking_id.button_validate()
        url = self.request_link()
        recipient = self.recipient('department_manager', self.department)
        mail_template = self.env.ref(
            'del_store_request.store_requisition_transfer')
        mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(
            self.id, force_send=True)

    def recipient(self, recipient, model):
        """Return recipient email address."""
        if recipient == 'hod':
            workmails = model.address_id, model.work_email
            workmail = {workmail for workmail in workmails if workmail}
            workmail = workmail.pop() if workmail else model.work_email
            if not isinstance(workmail, str):
                try:
                    return workmail.email
                except:
                    pass
            return workmail
        elif recipient == 'department_manager':
            manager = model.manager_id
            return manager.work_email or manager.address_id.email

    def request_link(self):
        pass
        # fragment = {}
        # base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        # model_data = self.env['ir.model.data']
        # fragment.update(base_url=base_url)
        # fragment.update(
        #     menu_id=model_data.get_object_reference('del_store_request', 'store_requisition_menu_1')[-1])
        # fragment.update(model='store.request')
        # fragment.update(view_type='form')
        # fragment.update(
        #     action=model_data.get_object_reference('del_store_request', 'store_action_window')[
        #         -1])
        # fragment.update(id=self.id)
        # query = {'db': self.env.cr.dbname}
        # res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        # return res

    def department_manager_reject(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'material.request.reject',
            'context': {'default_material_request_id': self.id},
            'view_mode': 'form',
            'target': 'new',
        }
    
    def warehouse_officer_reject(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'material.request.reject',
            'context': {'default_material_request_id': self.id},
            'view_mode': 'form',
            'target': 'new',
        }
    
    def post_reject_message(self, reason):
        for record in self:
            body = f"<h3>Subject: Material Requisition rejected by {self.env.user.name}<h3>\n<h4>Reason: {reason}</h4>"
            record.message_post(
                body=body,
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        return record.update({'state': 'reject'})
