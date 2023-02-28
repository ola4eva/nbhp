# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    state = fields.Selection(selection_add=[
        ('new', "Draft"),
        ('submit', "HOD To Approve"),
        ('hod', "Admin To Approve"),
        ('admin', "Admin Approved"),
        ('reject', 'Rejected'),
        ('done',)], default='new')

    def _default_employee(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)])

    requester_id = fields.Many2one(comodel_name='hr.employee', required=True, string='Requester',
                                   tracking=True, default=_default_employee, states={'draft': [('readonly', False)]})
    requester_department_id = fields.Many2one(
        comodel_name='hr.department', related='requester_id.department_id', string='Requester Department')

    requester_hod_id = fields.Many2one(
        comodel_name='hr.employee', related='requester_department_id.manager_id', string='Requester HOD')

    def do_scrap(self):
        self._check_company()
        for scrap in self:
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            # master: replace context by cancel_backorder
            move.with_context(is_scrap=True)._action_done()
            scrap.write({'move_id': move.id, 'state': 'done'})
            scrap.date_done = fields.Datetime.now()
        return True

    def button_submit(self):
        if not self.requester_hod_id:
            raise UserError(_("No HOD set for requesting department!"))

        self.name = self.env['ir.sequence'].next_by_code(
            'stock.scrap') or _('New')
        message = "Scrap Order {} requires your (HOD) Approval".format(
            self.name)
        partners_to_notify = self.requester_hod_id.user_id.partner_id
        self.notify_of_scrap_order(
            message=message, partner_ids=partners_to_notify.ids)
        self.state = 'submit'
        return True

    def button_hod_approve(self):
        message = "HOD Approved, Scrap Order {} requires your (Finance) Approval".format(
            self.name)
        group_iac = self.env.ref('account.group_account_manager')
        partners_to_notify = self.env['res.partner'].sudo()
        for user in group_iac.users:
            partners_to_notify += user.partner_id
        self.notify_of_scrap_order(
            message=message, partner_ids=partners_to_notify.ids)
        self.state = 'hod'
        return True

    def button_admin_approve(self):
        message = "Scrap Order {} has been Approved(Finance)".format(self.name)
        partners_to_notify = self.message_partner_ids
        self.notify_of_scrap_order(
            message=message, partner_ids=partners_to_notify.ids)
        self.state = 'admin'
        return self.action_validate()

    def button_reject(self):
        message = "Scrap Order {} has been rejected".format(self.name)
        partners_to_notify = self.message_partner_ids
        self.notify_of_scrap_order(
            message=message, partner_ids=partners_to_notify.ids)
        self.state = 'reject'
        return True

    def button_reset(self):
        self.state = 'new'

    def notify_of_scrap_order(self, message=None, partner_ids=[]):
        if not (message and partner_ids):
            return
        self.message_subscribe(partner_ids=partner_ids)
        self.message_post(subject=message, body=message,
                          partner_ids=partner_ids, subtype_xmlid="mail.mt_comment")
        return True
