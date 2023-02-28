# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', "Submitted"),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancel'),
        ('reject', 'Rejected'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)

    bom_sequence = fields.Char(
        string='Sequence No.', readonly=True, index=True, copy=False, default='New')
    bom_line_ids = fields.One2many('mrp.bom.line', 'bom_id', 'BoM Lines', copy=True, states={
                                   'draft': [('readonly', False)]}, readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('bom_sequence', 'New') == 'New':
            vals['bom_sequence'] = self.env['ir.sequence'].next_by_code(
                'mrp.bom') or '/'
        return super(MrpBom, self).create(vals)

    def button_submit(self):
        if self.bom_sequence == 'New':
            self.bom_sequence = self.env['ir.sequence'].next_by_code(
                'mrp.bom') or _('New')
        group_id = self.env.ref('nbhp_base.group_production_manager')
        partner_ids = []
        for user in group_id.users:
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "BOM '{}', needs approval".format(self.bom_sequence)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.state = 'submit'

    def button_confirm(self):
        self.state = 'confirmed'

    def button_cancel(self):
        self.state = 'cancel'

    def button_reject(self):
        self.state = 'reject'

    def button_reset(self):
        self.state = 'draft'
