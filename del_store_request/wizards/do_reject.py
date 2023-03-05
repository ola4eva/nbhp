from odoo import models, fields


class RejectMaterialRequisition(models.TransientModel):

    _name = 'material.request.reject'
    _description = 'Reject Material Request'

    material_request_id = fields.Many2one(
        'store.request', string='Material Requisition')
    reason = fields.Char('Reason', required=True)

    def confirm_rejection(self):
        return self.material_request_id.post_reject_message(self.reason)
