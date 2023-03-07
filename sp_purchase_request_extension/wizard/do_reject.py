from odoo import models, fields


class RejectPurchaseRequest(models.TransientModel):

    _name = "purchase.request.reject"
    _description = 'Reject Material Request'

    purchase_request_id = fields.Many2one(
        'sprogroup.purchase.request', string='Material Requisition')
    reason = fields.Char('Reason', required=True)

    def confirm_rejection(self):
        return self.purchase_request_id.post_reject_message(self.reason)
