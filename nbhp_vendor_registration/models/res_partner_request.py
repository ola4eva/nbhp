# -*- coding: utf-8 -*-

from odoo import models, fields, SUPERUSER_ID, api
import logging

_logger = logging.getLogger(__name__)


class ResPartnerRequest(models.Model):
    _name = 'res.partner.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Partner Request"

    name = fields.Char(string='Name', default="/",
                       readonly=True, compute="_compute_name")
    firstname = fields.Char('Firstname')
    lastname = fields.Char('Lastname')
    othername = fields.Char('Othername')
    email = fields.Char('Email')
    phone = fields.Char('Phone', required=True)
    date_of_birth = fields.Date('Date of Birth')
    street = fields.Char('Street')
    zipcode = fields.Char('Zip code')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    city = fields.Char('City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    state = fields.Selection([
        ('draft', 'New'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled'),
    ], string='State', default="draft")
    vendor_type = fields.Selection([
        ('person', "Individual"),
        ('company', "Company"),
    ], string="Individual/Company", required=True)

    def submit(self):
        self.state = 'confirm'

    def approve(self):
        self._create_vendor()
        self.state = 'approve'

    def cancel(self):
        self.state = "cancel"

    def reject(self):
        self.state = 'reject'

    def reset(self):
        self.state = 'draft'

    def _create_vendor(self):
        values = {
            'name': " ".join(self._get_name_list()),
            'phone': self.phone,
            'email': self.email,
            'street': self.street2,
            'city': self.city,
            'state_id': self.state_id and self.state_id.id,
            'country_id': self.country_id and self.country_id.id,
            'supplier_rank': 1,
            'company_type': self.vendor_type,

        }
        Partner = self.env['res.partner'].with_user(SUPERUSER_ID)
        try:
            partner_id = Partner.create(values)
        except KeyError:
            _logger.error("There was an error creating vendor...")
            partner_id = Partner
        return partner_id

    @api.depends("firstname", "lastname", "othername")
    def _compute_name(self):
        self.name = " ".join(
            self._get_name_list())

    def _get_name_list(self):
        return [name for name in [self.firstname or "", self.othername or "", self.lastname or ""] if name]
