# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools import get_lang


class SaleOrder(models.Model):
    _inherit = "sale.order"

    next_approved_by_user = fields.Many2many(
        "res.users", string="Current Approval Users", copy=False
    )
    next_approved_by_group = fields.Many2one(
        "res.groups", string="Current Approval Groups", copy=False
    )
    next_approval_line_id = fields.Many2one(
        "config.so.approval.line", string="Next Approval Line", copy=False
    )
    can_user_approve_order = fields.Boolean(
        string="Can User Approve Order?", compute="check_user_approve_order"
    )
    state = fields.Selection(
        selection_add=[
            ("to approve", "To Approve"),
            ("sale",),
            ("reject", "Rejected"),
            ("cancel",),
        ],
        string="state",
    )
    reject_user_id = fields.Many2one(
        comodel_name="res.users", string="Rejected by", readonly=True
    )

    order_line = fields.One2many(
        "sale.order.line",
        "order_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    user_id = fields.Many2one(
        "res.users", readonly=True, states={"draft": [("readonly", False)]}
    )
    payment_term_id = fields.Many2one(
        "account.payment.term", readonly=True, states={"draft": [("readonly", False)]}
    )
    date_order = fields.Datetime(readonly=True, states={
                                 "draft": [("readonly", False)]})
    partner_id = fields.Many2one(
        "res.partner", readonly=True, states={"draft": [("readonly", False)]}
    )
    fiscal_position_id = fields.Many2one(
        "account.fiscal.position",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    client_order_ref = fields.Char(
        readonly=True, states={"draft": [("readonly", False)]}
    )
    tag_ids = fields.Many2many(
        "crm.tag", readonly=True, states={"draft": [("readonly", False)]}
    )

    def button_cancel(self):
        for order in self:
            order.write(
                {
                    "next_approved_by_user": False,
                    "next_approved_by_group": False,
                    "next_approval_line_id": False,
                }
            )
        return super(SaleOrder, self).button_cancel()

    def action_reject(self):
        for order in self:
            order.write(
                {
                    "state": "reject",
                    "reject_user_id": self.env.uid,
                }
            )

    def action_validate(self):
        """This is the action that is called when a user creates a sales order and confirms it.

        The system checks for the dynamic configuration under company settings and finds the next approver either based on
        group or based on user. Once it finds the next approver, it sends an email to users in the group or the next user
        and sets the next approver.
        """
        for order in self:
            next_approval_line_id = order.find_order_approval()
            if next_approval_line_id:
                order.update_next_approval(next_approval_line_id)
            else:
                order.write(
                    {
                        "next_approved_by_user": False,
                        "next_approved_by_group": False,
                        "next_approval_line_id": False,
                    }
                )
            order.write({"state": "to approve"})

    def check_user_approve_order(self):
        for order in self:
            user_approve_order = False
            if order.state == "to approve":
                if self.env.user._is_admin():
                    user_approve_order = True
                if order.next_approved_by_user:
                    if self.env.user in order.next_approved_by_user:
                        user_approve_order = True
                if order.next_approved_by_group:
                    if order.next_approved_by_group in self.env.user.groups_id:
                        user_approve_order = True
                if order.user_has_groups("sales_team.group_sale_manager"):
                    user_approve_order = True
            order.can_user_approve_order = user_approve_order

    def do_sale_approve(self):
        for order in self:
            if order.state == "to approve":
                if order.next_approved_by_user:
                    if (
                        not self.env.user._is_admin()
                        and self.env.user not in order.next_approved_by_user
                    ):
                        raise UserError(
                            _("You don't have rights to approved order."))
                if order.next_approved_by_group:
                    if (
                        not self.env.user._is_admin()
                        and order.next_approved_by_group not in self.env.user.groups_id
                    ):
                        raise UserError(
                            _("You don't have rights to approved order."))

                next_approval_line_id = order.find_order_approval(
                    order.next_approval_line_id
                )
                if next_approval_line_id:
                    order.update_next_approval(next_approval_line_id)
                else:
                    order.write(
                        {
                            "next_approved_by_user": False,
                            "next_approved_by_group": False,
                            "next_approval_line_id": False,
                        }
                    )
                    order.action_confirm()

    def update_next_approval(self, next_approval_line_id):
        approve_by = next_approval_line_id.config_approval_id.approve_by
        users_ids = group_id = False
        if approve_by == "user":
            users_ids = next_approval_line_id.mapped("res_user_ids")
        else:
            group_id = next_approval_line_id.mapped("res_group_id")

        update_vals = {
            "state": "to approve",
            "next_approval_line_id": next_approval_line_id.id,
        }
        update_vals["next_approved_by_user"] = (
            [(6, 0, users_ids.ids)] if users_ids else False
        )
        update_vals["next_approved_by_group"] = group_id.id if group_id else False

        user_ids = users_ids if users_ids else group_id.mapped("users")
        if user_ids:

            partner_ids = []
            for user in user_ids:
                partner_ids.append(user.partner_id.id)
            self.message_subscribe(partner_ids=partner_ids)

            msg = _("Dear %s, <br/> Please approve sales order %s.") % (
                ", ".join([str(user.name) for user in user_ids]),
                self.name,
            )
            self.message_post(body=msg, partner_ids=partner_ids)
        self.write(update_vals)

    def button_confirm(self):
        for order in self:
            next_approval_line_id = order.find_order_approval()
            if next_approval_line_id:
                order.update_next_approval(next_approval_line_id)
            else:
                order.write(
                    {
                        "next_approved_by_user": False,
                        "next_approved_by_group": False,
                        "next_approval_line_id": False,
                    }
                )
                return super(SaleOrder, self).button_confirm()
        return True

    def find_order_approval(self, approval_line_id=None):
        next_approval_line_id = False
        company_id = self.company_id.sudo()
        so_approval_ids = company_id.config_so_approval_ids
        if not so_approval_ids:
            return next_approval_line_id

        main_curreny_total = self.amount_total
        if self.currency_id.id != company_id.currency_id.id:
            main_curreny_total = self.currency_id._convert(
                self.amount_total,
                company_id.currency_id,
                company_id,
                self.date_order or fields.Date.today(),
            )

        find_approval_id = so_approval_ids.filtered(
            lambda l: main_curreny_total >= l.min_amount
            and main_curreny_total <= l.max_amount
        )
        if find_approval_id:
            approval_line_ids = find_approval_id.approval_line_ids
            if (
                approval_line_id
                and approval_line_id.config_approval_id.id == find_approval_id.id
                and find_approval_id.approval_line_ids.filtered(
                    lambda l: l.sequence == approval_line_id.sequence
                )
            ):
                approval_line_ids = find_approval_id.approval_line_ids.filtered(
                    lambda l: l.sequence > approval_line_id.sequence
                )
            if not approval_line_ids:
                return next_approval_line_id

            next_approval_line_id = approval_line_ids[0]
        else:
            next_approval_line_id = False
        return next_approval_line_id

    @api.constrains("date_order")
    def _check_date_order(self):
        if self.date_order:
            if self.date_order > datetime.now():
                raise UserError(
                    _("You are not allowed to post into a future date"))


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    name = fields.Char(readonly=True, states={"draft": [("readonly", False)]})
    price_unit = fields.Float(readonly=True, states={
                              "draft": [("readonly", False)]})
    product_uom_qty = fields.Float(
        readonly=True, states={"draft": [("readonly", False)]}
    )
    tax_id = fields.Many2many(
        "account.tax", readonly=True, states={"draft": [("readonly", False)]}
    )

    @api.onchange('product_id')
    def _onchange_product_id_warning(self):
        if not self.product_id:
            return
        product = self.product_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.order_partner_id.lang).code,
            partner_id=self.order_partner_id.id,
            company_id=self.company_id.id,
        )
        self.name = self._get_product_purchase_description(product_lang)
        if product.sale_line_warn != 'no-message':
            if product.sale_line_warn == 'block':
                self.product_id = False

            return {
                'warning': {
                    'title': _("Warning for %s", product.name),
                    'message': product.sale_line_warn_msg,
                }
            }

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        return name


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
