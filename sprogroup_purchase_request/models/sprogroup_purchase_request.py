# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_STATES = [
    ("draft", "Draft"),
    ("to_approve", "To be approved"),
    ("leader_approved", "Line-Manager Approved"),
    ("manager_approved", "Procurement Approved"),
    # ("iac_approved", "IAC Approved"),
    ("rejected", "Rejected"),
    ("done", "Done"),
]


class SprogroupPurchaseRequest(models.Model):

    _name = "sprogroup.purchase.request"
    _description = "Sprogroup Purchase Request"
    _inherit = ["mail.thread"]

    @api.model
    def _get_default_requested_by(self):
        return self.env["res.users"].browse(self.env.uid)

    @api.model
    def _get_default_name(self):
        return self.env["ir.sequence"].next_by_code(
            "sprogroup.purchase.request"
        )

    @api.model
    def _get_default_approver(self):
        self = self.sudo()
        requester = self._get_default_requested_by()
        employee_id = self.env["hr.employee"].search(
            [('user_id', '=', requester.id)])
        manager_id = employee_id.parent_id if employee_id.parent_id else employee_id.department_id.manager_id
        default_approver_id = manager_id and manager_id.user_id.id or False
        return default_approver_id

    name = fields.Char(
        "Request Name", size=32,
        # required=True,
        tracking=True
    )
    code = fields.Char(
        "Code",
        size=32,
        required=True,
        default=_get_default_name,
        tracking=True,
    )
    date_start = fields.Date(
        "Start date",
        help="Date when the user initiated the request.",
        default=fields.Date.context_today,
        tracking=True,
    )
    end_start = fields.Date(
        "End date",
        default=fields.Date.context_today,
        tracking=True,
    )
    requested_by = fields.Many2one(
        "res.users",
        "Requested by",
        required=True,
        tracking=True,
        default=_get_default_requested_by,
    )
    assigned_to = fields.Many2one(
        "res.users", "Approver (Line-Manager)",
        required=True,
        default=_get_default_approver,
        tracking=True
    )
    description = fields.Text("Description")

    line_ids = fields.One2many(
        "sprogroup.purchase.request.line",
        "request_id",
        "Products to Purchase",
        readonly=False,
        copy=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=_STATES,
        string="Status",
        index=True,
        tracking=True,
        required=True,
        copy=False,
        default="draft",
    )

    @api.depends("requested_by")
    def _compute_department(self):
        if self.requested_by.id == False:
            self.requested_by = self.env.uid

        employee = self.env["hr.employee"].search(
            ['|', ('user_id', '=', self.env.uid), ("work_email", "=", self.requested_by.email)], limit=1
        )
        if len(employee) > 0:
            self.department_id = employee[0].department_id.id
        else:
            self.department_id = None

    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        compute="_compute_department",
        store=True,
    )

    @api.depends("state")
    def _compute_can_leader_approved(self):
        current_user_id = self.env.uid
        if (
            self.state == "to_approve"
            and current_user_id == self.assigned_to.id
        ):
            self.can_leader_approved = True
        else:
            self.can_leader_approved = False

    can_leader_approved = fields.Boolean(
        string="Can Leader approved", compute="_compute_can_leader_approved"
    )

    @api.depends("state")
    def _compute_can_manager_approved(self):
        current_user = self.env["res.users"].browse(self.env.uid)
        if self.state == "leader_approved" and current_user.has_group(
            "purchase.group_purchase_user"
        ):
            self.can_manager_approved = True
        else:
            self.can_manager_approved = False

    can_manager_approved = fields.Boolean(
        string="Can Manager approved", compute="_compute_can_manager_approved"
    )

    @api.depends("state")
    def _compute_can_iac_approved(self):
        current_user = self.env["res.users"].browse(self.env.uid)

        if self.state == "manager_approved" and current_user.has_group(
            "sprogroup_purchase_request.group_sprogroup_purchase_request_manager"
        ):
            self.can_iac_approved = True
        else:
            self.can_iac_approved = False

    can_iac_approved = fields.Boolean(
        string="Can IAC approved", compute="_compute_can_iac_approved"
    )

    @api.depends("state")
    def _compute_can_reject(self):
        self.can_reject = (
            self.can_leader_approved
            or self.can_manager_approved
            or self.can_iac_approved
        )

    can_reject = fields.Boolean(
        string="Can reject", compute="_compute_can_reject"
    )

    @api.depends("state")
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in (
                "to_approve",
                "leader_approved",
                "manager_approved",
                "rejected",
                "done",
            ):
                rec.is_editable = False
            else:
                rec.is_editable = True

    is_editable = fields.Boolean(
        string="Is editable", compute="_compute_is_editable", readonly=True
    )

    @api.model
    def create(self, vals):
        request = super(SprogroupPurchaseRequest, self).create(vals)
        if vals.get("assigned_to"):
            request.message_subscribe(
                partner_ids=[request.assigned_to.partner_id.id]
            )
        return request

    def write(self, vals):
        res = super(SprogroupPurchaseRequest, self).write(vals)
        for request in self:
            if vals.get("assigned_to"):
                self.message_subscribe(
                    partner_ids=[request.assigned_to.partner_id.id]
                )
        return res

    def _get_message(self):
        message = ""
        if self.name:
            message = "Purchase Request '{}-{}' requires your Approval".format(
                self.name, self.code)
        else:
            message = "Purchase Request '{}' requires your Approval".format(
                self.code)
        return message

    def button_draft(self):
        self.mapped("line_ids").do_uncancel()
        return self.write({"state": "draft"})

    def button_to_approve(self):
        message = self._get_message()
        partners_to_notify = self.env['res.partner'].sudo()
        partners_to_notify += self.assigned_to.partner_id
        self.notify_of_pr_order(
            message=message, partner_ids=partners_to_notify.ids)
        return self.write({"state": "to_approve"})

    def button_leader_approved(self):
        message = self._get_message()
        group_purchase_user = self.env.ref('purchase.group_purchase_user')
        partners_to_notify = self.env['res.partner'].sudo()
        for user in group_purchase_user.users:
            partners_to_notify += user.partner_id
        self.notify_of_pr_order(
            message=message, partner_ids=partners_to_notify.ids)
        return self.write({"state": "leader_approved"})

    def button_manager_approved(self):
        return self.write({"state": "manager_approved"})

    def button_rejected(self):
        self.mapped("line_ids").do_cancel()
        return self.write({"state": "rejected"})

    def button_done(self):
        return self.write({"state": "done"})

    def check_auto_reject(self):
        """When all lines are cancelled the purchase request should be
        auto-rejected."""
        for pr in self:
            if not pr.line_ids.filtered(lambda l: l.cancelled is False):
                pr.write({"state": "rejected"})

    def notify_of_pr_order(self, message=None, partner_ids=[]):
        if not (message and partner_ids):
            return
        self.message_subscribe(partner_ids=partner_ids)
        self.message_post(subject=message, body=message,
                          partner_ids=partner_ids, subtype_xmlid="mail.mt_comment")
        return True

    #attachment = fields.Binary('Attachment', attachment=True)
    #attachment_name = fields.Char('Attachment Name')

    # @api.depends("attachment")
    # def _create_attachment(self):
    #     for rec in self:
    #         if rec.attachment:
    #             ir_attachment_obj = self.env["ir.attachment"]
    #             ir_attachment_obj.sudo().create({
    #                 'name': rec.attachment_name,
    #                 'store_fname': rec.attachment_name,
    #                 'res_name': rec.attachment_name,
    #                 'type': 'binary',
    #                 'res_model': 'sprogroup.purchase.request',
    #                 'res_id': rec.id,
    #                 'datas': rec.attachment
    #             })

    def make_purchase_quotation(self):
        view_id = self.env.ref("purchase.purchase_order_form")

        order_line = []
        for line in self.line_ids:
            product = line.product_id
            fpos = self.env["account.fiscal.position"]
            if self.env.uid == SUPERUSER_ID:
                company_id = self.env.user.company_id.id
                taxes_id = fpos.map_tax(
                    line.product_id.supplier_taxes_id.filtered(
                        lambda r: r.company_id.id == company_id
                    )
                )
            else:
                taxes_id = fpos.map_tax(line.product_id.supplier_taxes_id)

            product_line = (
                0,
                0,
                {
                    "product_id": line.product_id.id,
                    "state": "draft",
                    "product_uom": line.product_id.uom_po_id.id,
                    "price_unit": 0,
                    "date_planned": datetime.today().strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    ),
                    # 'taxes_id' : ((6,0,[taxes_id.id])),
                    "product_qty": line.product_qty,
                    "name": line.product_id.name,
                },
            )
            order_line.append(product_line)

        return {
            "name": _("New Quotation"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "view_id": view_id.id,
            "views": [(view_id.id, "form")],
            "context": {
                "default_order_line": order_line,
                "default_state": "draft",
                "default_origin": self.name,
            },
        }


class SprogroupPurchaseRequestLine(models.Model):

    _name = "sprogroup.purchase.request.line"
    _description = "Sprogroup Purchase Request Line"
    _inherit = ["mail.thread"]

    @api.depends(
        "product_id",
        "name",
        "product_uom_id",
        "product_qty",
        "date_required",
        "specifications",
    )
    def _compute_supplier_id(self):
        for rec in self:
            if rec.product_id:
                if rec.product_id.seller_ids:
                    rec.supplier_id = rec.product_id.seller_ids[0].name

    product_id = fields.Many2one(
        "product.product",
        "Product",
        domain=[("purchase_ok", "=", True)],
        required=True,
        tracking=True,
    )
    name = fields.Char("Description", size=256, tracking=True)
    product_uom_id = fields.Many2one(
        "uom.uom", "Product Unit of Measure", tracking=True
    )
    product_qty = fields.Float(
        string="Quantity",
        tracking=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    request_id = fields.Many2one(
        "sprogroup.purchase.request",
        "Purchase Request",
        ondelete="cascade",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", store=True, readonly=True
    )

    requested_by = fields.Many2one(
        "res.users",
        related="request_id.requested_by",
        string="Requested by",
        store=True,
        readonly=True,
    )
    assigned_to = fields.Many2one(
        "res.users",
        related="request_id.assigned_to",
        string="Assigned to",
        store=True,
        readonly=True,
    )
    date_start = fields.Date(
        related="request_id.date_start",
        string="Request Date",
        readonly=True,
        store=True,
    )
    end_start = fields.Date(
        related="request_id.end_start",
        string="End Date",
        readonly=True,
        store=True,
    )
    description = fields.Text(
        related="request_id.description",
        string="Description",
        readonly=True,
        store=True,
    )
    date_required = fields.Date(
        string="Request Date",
        required=True,
        tracking=True,
        default=fields.Date.context_today,
    )

    specifications = fields.Text(string="Specifications")
    request_state = fields.Selection(
        string="Request state",
        readonly=True,
        related="request_id.state",
        selection=_STATES,
        store=True,
    )
    supplier_id = fields.Many2one(
        "res.partner",
        string="Preferred supplier",
        compute="_compute_supplier_id",
    )

    cancelled = fields.Boolean(
        string="Cancelled", readonly=True, default=False, copy=False
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = "[%s] %s" % (name, self.product_id.code)
            if self.product_id.description_purchase:
                name += "\n" + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1
            self.name = name

    def do_cancel(self):
        """Actions to perform when cancelling a purchase request line."""
        self.write({"cancelled": True})

    def do_uncancel(self):
        """Actions to perform when uncancelling a purchase request line."""
        self.write({"cancelled": False})

    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in (
                "to_approve",
                "leader_approved",
                "manager_approved",
                # "iac_approved",
                "rejected",
                "done",
            ):
                rec.is_editable = False
            else:
                rec.is_editable = True

    is_editable = fields.Boolean(
        string="Is editable", compute="_compute_is_editable", readonly=True
    )

    def write(self, vals):
        res = super(SprogroupPurchaseRequestLine, self).write(vals)
        if vals.get("cancelled"):
            requests = self.mapped("request_id")
            requests.check_auto_reject()
        return res
