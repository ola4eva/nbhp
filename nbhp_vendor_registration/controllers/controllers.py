# -*- coding: utf-8 -*-
# from odoo import http


# class NbhpVendorRegistration(http.Controller):
#     @http.route('/nbhp_vendor_registration/nbhp_vendor_registration', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/nbhp_vendor_registration/nbhp_vendor_registration/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('nbhp_vendor_registration.listing', {
#             'root': '/nbhp_vendor_registration/nbhp_vendor_registration',
#             'objects': http.request.env['nbhp_vendor_registration.nbhp_vendor_registration'].search([]),
#         })

#     @http.route('/nbhp_vendor_registration/nbhp_vendor_registration/objects/<model("nbhp_vendor_registration.nbhp_vendor_registration"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('nbhp_vendor_registration.object', {
#             'object': obj
#         })
