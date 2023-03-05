# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError

# from urlparse import urljoin
# from urllib import urlencode

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
        ('approved', 'Central Warehouse Manager Approval'),
        # ('warehouse', 'Warehouse Officer'),
        ('approval', 'Warehouse Owner'),
        ('transfer', 'Transfer'),
        ('done', 'Done'),
        ('receive', 'Received')
    ]

    # def get_default_values(self):
    #     hr_employee = self.env['hr.em'].search([('user_id', '=', self._current_login_user())], limit=1)

    # company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', store=True,
    #                              readonly=True,
    #                              default=lambda self: self.env.user.company_id)

    def _current_login_employee(self):
        """Get the employee record related to the current login user."""
        hr_employee = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        print(hr_employee)
        print(self.env.uid)
        print(self.env.user.id)
        return hr_employee.id

    @api.onchange('end_user')
    def get_hod_from_end_user(self):
        if self.end_user:
            self.hod=self.end_user.department_id.manager_id.id

    # @api.model
    # def default_get(self, fields):
    #     defaults = super(StoreRequest, self).default_get(fields)
    #     if defaults.get('kkk')==True:
    #         print(fields)
    #         print(defaults.get('kkk'))


    name = fields.Char(string='Number', default='/')
    state = fields.Selection(selection=REQUEST_STAGE, default='draft', track_visibility='onchange')
    requester = fields.Many2one('res.users', string='Requester', default=_current_login_user,
                                track_visibility='onchange')
    end_user = fields.Many2one('hr.employee', string='End User',required=True,store=True)
    request_date = fields.Datetime(string='Request Date', default=lambda self: datetime.now(),
                                   help='The day in which request was initiated')
    request_deadline = fields.Datetime(string='Request Deadline')
    hod = fields.Many2one('hr.employee', string='H.O.D',store=True)
    department = fields.Many2one('hr.department', related='end_user.department_id', string='Department')
    dst_location_id = fields.Many2one('stock.location', string='Destination Location',
                                      help='Departmental Stock Location', track_visibility='onchange',required=False,
                                      domain=[('usage','!=','view')])
    src_location_id = fields.Many2one('stock.location', string='Source Location',
                                      help='Departmental Stock Location', track_visibility='onchange'
                                      , default = lambda self: self.env.user.company_id.source_location if(self.kkk == True) else None)
    kkk=fields.Boolean("Internal  Request")
    # , default = lambda self: self.env.user.company_id.source_location
    # request_ids = fields.One2many('ng.ir.request.line', inverse_name='request_id', string='Request Line',
    #                               required=True)
    approve_request_ids = fields.One2many('store.request.approve', 'request_id',string='Request Line', required=True)
    reason = fields.Text(string='Rejection Reason')
    availaibility = fields.Boolean(string='Availaibility', compute='_compute_availabilty')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   default=lambda self: self.env.user.company_id.warehouse_id if(self.kkk == True) else None)
    # company_id = fields.Many2one('res.company', 'Company',
    #                              default=lambda self: self.env['res.company']._company_default_get(),
    #                              index=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)

    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    transit_location_id=fields.Many2one('stock.location',string="Transit Location",domain=[('usage','=','transit')],
                                        default=lambda self: self.env.user.company_id.transit_location)
    stock_picking_type=fields.Many2one('stock.picking.type',string="Stock Picking Type"
                                       ,default=lambda self: self.env.user.company_id.stock_picking_type)

    @api.depends('approve_request_ids')
    # @api.one
    def _compute_availabilty(self):
        count_total = len(self.approve_request_ids)
        count_avail = len([appr_id.state for appr_id in self.approve_request_ids if appr_id.state == 'available'])
        self.availaibility = count_total == count_avail

    # @api.onchange('hod')
    # def _onchange_hod(self):
    #     if self.department:
    #         self.dst_location_id = self.department.location_id

    # @api.model
    # def create(self, vals):
    #     rec_id = super(StoreRequest, self).create(vals)
    #     return rec_id

    # @api.multi
    def submit(self):
        # if not self.request_ids:
        #     raise UserError('You can not submit an empty item list for requisition.')
        # else:
            # fetch email template.
        seq = self.env['ir.sequence'].next_by_code('store.request')
        recipient = self.recipient('hod', self.hod)
        url = self.request_link()
        mail_template = self.env.ref('del_store_request.store_requisition_submit')
        mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(self.id, force_send=True)
        self.write({'state': 'submit', 'name': seq})

    #         self.dst_location_id = self.department.loca
    # @api.multi
    def department_manager_approve(self):
        if self:
            # approved = context.get('approved')
            # if not approved:
            #     # send rejection mail to the author.
            #     return {
            #         "type": "ir.actions.act_window",
            #         "res_model": 'store.wizard',
            #         "views": [[False, "form"]],
            #         "context": {'request_id': self.id},
            #         "target": "new",
            #     }
            # else:
            #     # move to next level and send mail
            url = self.request_link()
            recipient = self.recipient('department_manager', self.department)
            mail_template = self.env.ref('del_store_request.store_requisition_approval')
            mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(self.id, force_send=True)
            self.write({'state': 'approved'})

    # @api.multi
    def main_manager_approve(self):
        # approved = context.get('approved')
        # if not approved:
        #     # send mail to the author.
        #     return {
        #         "type": "ir.actions.act_window",
        #         "res_model": 'store.wizard',
        #         "views": [[False, "form"]],
        #         "context": {'request_id': self.id},
        #         "target": "new",
        #     }
        # else:
        # move to next level and send mail
        self.write({'state': 'approval'})

    # @api.multi
    def warehouse_officer_confirm(self):
        if not self.approve_request_ids:
            raise UserError('Please add requested items.')
        else:
            url = self.request_link()
            recipient = self.recipient('department_manager', self.department)
            mail_template = self.env.ref('del_store_request.store_requisition_warehouse_officer')
            mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(self.id, force_send=True)
            self.write({'state': 'approval'})

    # @api.multi
    def warehouse_officer_confirm_qty(self):
        for con in self.approve_request_ids:
            if con.qty >= con.quantity:
                raise ValidationError("Requested Quantity Available")
            elif con.qty < con.quantity:
                raise ValidationError("Available Quantity not enough click to procure")
        # """Forward the available quantity to warehouse officer."""
        # # clone = self.copy()
        # available_aggregate = sum([approve_request_id.qty for approve_request_id in self.approve_request_ids])
        # if available_aggregate <= 0:
        #     raise UserError('The item line is empty or quantity available can not be forwarded.')
            # return False
        # if self.approve_request_ids:
        #     for index, approve_request_id in enumerate(self.approve_request_ids):
        #         approve_id = approve_request_id.copy()
        #         availqty, reqqty = approve_id.qty, approve_id.quantity
        #         if availqty <= reqqty:
        #             approve_id.write({'request_id': clone.id, 'quantity': availqty})
                    # self.approve_request_ids[index].write({'quantity': reqqty - availqty})
                # else:  # Detach from self record
                #     approve_id.sudo().unlink()
            # for request_id in self.request_ids:
            #     req = request_id.copy()
            #     req.write({'request_id': clone.id})
            # clone.write({'state': 'approval', 'name': self.name})
        # if not clone.approve_request_ids:
        #     clone.sudo().unlink()
        #     raise ValidationError('There is enough quantity available for confirmation, make use of the confirm button.')
            # return False
            # return {
            #     "type": "ir.actions.act_window",
            #     "res_model": 'store.request',
            #     "views": [[False, "form"]],
            #     "context": {'request_id': self.id},
            #     "res_id": clone.id,
            #     "target": "main",
            # }
        # else:
        #     raise ValidationError('No line item(s) defined.')

    # @api.onchange('warehouse_id')
    # def when_name_onchange(self):
    #     print("delebeat")
    #     self.src_location_id = False
    #     if self.warehouse_id:
    #         self.src_location_id = False
    #         return {'domain': {'src_location_id': [('warehouse_id', '=', self.warehouse_id.id)]}}
    #     else:
    #         self.src_location_id = False
    #         return {'domain': {'src_location_id': False}}



    # @api.multi
    def confirmation(self):
        # approved = context.get('approved')
        # if not approved:
        #     # send mail to the author.
        #     return {
        #         "type": "ir.actions.act_window",
        #         "res_model": 'store.wizard',
        #         "views": [[False, "form"]],
        #         "context": {'request_id': self.id},
        #         "target": "new",
        #     }
        # else:
            # move to next level and send mail
        if self.src_location_id.stock_user_id.id != self.env.uid:
            raise ValidationError("You are not the warehouse owner")

        self.write({'state': 'transfer'})


    # @api.multi
    def do_transfer_receive(self):
        for con in self.approve_request_ids:
            if not con.received_qty:
                raise ValidationError("Quantity received not entered")
            # if con.quantity >con.received_qty:
                # raise ValidationError("Quantity Received must be equal to  Quantity  Requested")

        if self.requester.id != self.env.user.id:
            print(self.env.user.id,self.requester.id)
            raise ValidationError('You are not the Requester')
        if not self.dst_location_id:
            raise ValidationError("Pls select a Destination Location")
        if self:
            src_location_id = self.src_location_id.id
            dst_location_id = self.dst_location_id.id
            transit_location_id = self.transit_location_id.id
            domain = [
                ('code', '=', 'internal'),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('active', '=', True)
            ]
            stock_picking = self.env['stock.picking']
            picking_type = self.env['stock.picking.type'].search(domain, limit=1)
            print(picking_type)
            payload = {
                'location_id': transit_location_id,
                'location_dest_id': dst_location_id,
                'picking_type_id': picking_type.id
            }
            stock_picking_id = stock_picking.create(payload)
            move_id = self.stock_move_received(self.approve_request_ids, stock_picking_id)
            self.process(stock_picking_id)
            stock_picking_id.action_confirm()
            stock_picking_id.action_set_quantities_to_reservation()
            stock_picking_id.button_validate()

    # @api.multi
    def do_transfer(self):
        if not self.transit_location_id:
            raise ValidationError("Pls select a Transit Location")
        if self:
            src_location_id = self.src_location_id.id
            dst_location_id = self.dst_location_id.id
            transit_location_id = self.transit_location_id.id
            domain = [
                ('code', '=', 'internal'),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('active', '=', True)
            ]
            stock_picking = self.env['stock.picking']
            picking_type = self.env['stock.picking.type'].search(domain, limit=1)
            print(picking_type)
            payload = {
                'location_id': src_location_id,
                'location_dest_id': transit_location_id,
                'picking_type_id': picking_type.id
            }
            stock_picking_id = stock_picking.create(payload)
            move_id = self.stock_move(self.approve_request_ids, stock_picking_id)
            # self.process(stock_picking_id)
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
                    raise UserError(("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
        # for pack in picking_id.pack_operation_ids:
        #     if pack.product_qty > 0:
        #         pack.write({'qty_done': pack.product_qty})
        #     else:
        #         pack.unlink()
        picking_id.button_validate()
        url = self.request_link()
        recipient = self.recipient('department_manager', self.department)
        mail_template = self.env.ref('del_store_request.store_requisition_transfer')
        mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(self.id, force_send=True)

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