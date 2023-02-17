# -*- coding: utf-8 -*-

from odoo import models, fields, _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=[('submit', "Store Office Approval"), 
        ('warehouse_officer_approval', "Warehouse Officer Approval"), 
        ('quality_officer_approval', "Quality Officer Approval"),
        ('production_manager_approval', "Production Manager Approval"),
        ('factory_manager_approval', "Factory Manager Approval"), ('sale',)])

    def submit(self):
        group_sale_manager = self.env.ref('nbhp_base.group_store_officer')
        message = "Sales Order {} requires your Store Office approval".format(self.name)
        partners_to_notify = self.env['res.partner'].sudo()
        for user in group_sale_manager.users:
            partners_to_notify += user.partner_id
        self.notify_of_sale_order(
            message=message, partner_ids=partners_to_notify.ids)
        self.state = 'submit'
        return True

    def approve_store_office(self):
        group_account = self.env.ref('nbhp_base.group_warehouse_officer')
        message = "Sales Order {} requires your Warehouse Approval".format(self.name)
        partners_to_notify = self.env['res.partner'].sudo()
        for user in group_account.users:
            partners_to_notify += user.partner_id
        self.notify_of_sale_order(
            message=message, partner_ids=partners_to_notify.ids)
        self.state = 'warehouse_officer_approval'
        return True

    def approve_warehouse_officer(self):
        group_account = self.env.ref('nbhp_base.group_quality_officer')
        message = "Sales Order {} requires your Quality Approval".format(self.name)
        partners_to_notify = self.env['res.partner'].sudo()
        for user in group_account.users:
            partners_to_notify += user.partner_id
        self.notify_of_sale_order(
            message=message, partner_ids=partners_to_notify.ids)
        self.state = 'quality_officer_approval'
        return True

    def approve_quality_officer(self):
        group_account = self.env.ref('nbhp_base.group_production_manager')
        message = "Sales Order {} requires your Production Approval".format(self.name)
        partners_to_notify = self.env['res.partner'].sudo()
        for user in group_account.users:
            partners_to_notify += user.partner_id
        self.notify_of_sale_order(
            message=message, partner_ids=partners_to_notify.ids)
        self.state = 'production_manager_approval'
        return True

    def approve_production_manager(self):
        group_account = self.env.ref('nbhp_base.group_factory_manager')
        message = "Sales Order {} requires your Factory Approval".format(self.name)
        partners_to_notify = self.env['res.partner'].sudo()
        for user in group_account.users:
            partners_to_notify += user.partner_id
        self.notify_of_sale_order(
            message=message, partner_ids=partners_to_notify.ids)
        self.state = 'factory_manager_approval'
        return True

    def approve(self):
        for rec in self:
            rec.action_confirm()

    def action_reject(self):
        message = "Sales Order {} has been rejected".format(self.name)
        partners_to_notify = self.message_partner_ids
        self.notify_of_sale_order(
            message=message, partner_ids=partners_to_notify.ids)
        self.action_cancel()

    def notify_of_sale_order(self, message=None, partner_ids=[]):
        if not (message and partner_ids):
            return
        self.message_subscribe(partner_ids=partner_ids)
        self.message_post(subject=message, body=message,
                          partner_ids=partner_ids, subtype_xmlid="mail.mt_comment")
        return True