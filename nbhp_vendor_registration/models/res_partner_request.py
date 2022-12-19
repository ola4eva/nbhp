# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerRequest(models.Model):
    _name = 'res.partner.request'
    _description = "Partner Request"

    firstname = fields.Char('Firstname')
    lastname = fields.Char('Lastname')
    othername = fields.Char('Othername')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    date_of_birth = fields.Date('Date of Birth')
    street = fields.Char('street')
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
    ], string='State', default="draft")
