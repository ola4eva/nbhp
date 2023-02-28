# -*- coding: utf-8 -*-
from odoo import http

# class DelStoreRequest(http.Controller):
#     @http.route('/del_store_request/del_store_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/del_store_request/del_store_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('del_store_request.listing', {
#             'root': '/del_store_request/del_store_request',
#             'objects': http.request.env['del_store_request.del_store_request'].search([]),
#         })

#     @http.route('/del_store_request/del_store_request/objects/<model("del_store_request.del_store_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('del_store_request.object', {
#             'object': obj
#         })