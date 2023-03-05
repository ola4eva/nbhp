# -*- coding: utf-8 -*-

from odoo import models


class PurchaseRequest(models.Model):
    _inherit = 'sprogroup.purchase.request'

    def button_rejected(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request.reject',
            'context': {'default_purchase_request_id': self.id},
            'view_mode': 'form',
            'target': 'new',
        }

    def post_reject_message(self, reason):
        for record in self:
            record.mapped("line_ids").do_cancel()
            body = f"<h3>Subject: Purchase Request rejected by {self.env.user.name}<h3>\n<h4>Reason: {reason}</h4>"
            record.message_post(
                body=body,
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        return record.update({'state': 'rejected'})
