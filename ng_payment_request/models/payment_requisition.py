from odoo import fields, models, api, _, exceptions
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class AccountMoveInherit(models.Model):
    """docstring for ClassName"""
    _inherit = 'account.move.line'

    customer_id = fields.Many2one(
        comodel_name="res.partner", string="Customer/Vendor")


class payment_request_line(models.Model):
    _name = "payment.requisition.line"
    _description = "Cash Requisition Line"

    @api.depends('payment_request_id')
    def check_state(self):
        self.dummy_state = self.payment_request_id.state

    name = fields.Char('Description', required=True)
    request_amount = fields.Float('Requested Amount', required=True)
    approved_amount = fields.Float('Approved Amount')
    payment_request_id = fields.Many2one(
        'payment.requisition', string="Payment Request")
    expense_account_id = fields.Many2one('account.account', 'Account')
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account')
    credit_account_id = fields.Many2one(
        comodel_name='account.account', string='Pay From')
    dummy_state = fields.Char(compute='check_state', string='State')
    partner_id = fields.Many2one('res.partner', string="Customer/Vendor")

    @api.onchange('request_amount')
    def _get_request_amount(self):
        if self.request_amount:
            amount = self.request_amount
            self.approved_amount = amount


class payment_request(models.Model):
    _inherit = ['mail.thread']
    _name = "payment.requisition"
    _description = 'Cash Requisition'

    @api.depends('request_line', 'request_line.request_amount', 'request_line.approved_amount')
    def _compute_requested_amount(self):
        for record in self:
            requested_amount, approved_amount = 0, 0
            for line in record.request_line:
                requested_amount += line.request_amount
                approved_amount += line.approved_amount

            record.amount_company_currency = requested_amount
            record.requested_amount = requested_amount
            record.approved_amount = approved_amount
            company_currency = record.company_id.currency_id
            current_currency = record.currency_id
            if company_currency != current_currency:
                amount = company_currency.compute(
                    requested_amount, current_currency)
                record.amount_company_currency = amount

    name = fields.Char('Name', default="/", copy=False)
    requester_id = fields.Many2one(
        'res.users', 'Requester', required=True, default=lambda self: self.env.user)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    department_id = fields.Many2one('hr.department', 'Department')
    date = fields.Date('Request Date', default=fields.Date.context_today)
    description = fields.Text('Description')
    bank_id = fields.Many2one('res.bank', 'Bank')
    bank_account = fields.Char('Bank Account', copy=False)
    request_line = fields.One2many(
        'payment.requisition.line', 'payment_request_id', string="Lines", copy=False)
    requested_amount = fields.Float(
        compute="_compute_requested_amount", string='Requested Amount', store=True, copy=False)
    approved_amount = fields.Float(
        compute="_compute_requested_amount", string='Approved Amount', store=True, copy=False)
    amount_company_currency = fields.Float(
        compute="_compute_requested_amount", string='Amount In Company Currency', store=True, copy=False)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('payment.requisition'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('mgr_approve', 'GM To Approve'),
        ('gm_approve', 'MD To Approve'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('refused', 'Refused'),
        ('cancelled', 'Cancelled')
    ], tracking=True, default="draft", string="State")
    need_gm_approval = fields.Boolean(
        'Needs First Approval?', copy=False, readonly=True)
    need_md_approval = fields.Boolean(
        'Needs Final Approval?', copy=False, readonly=True)
    general_manager_id = fields.Many2one(
        'hr.employee', 'General Manager', readonly=True)
    manging_director_id = fields.Many2one(
        'hr.employee', 'Managing Director', readonly=True)
    dept_manager_id = fields.Many2one(
        'hr.employee', 'Department Manager', readonly=True)
    dept_manager_approve_date = fields.Date(
        'Approved By Department Manager On', readonly=True)
    gm_approve_date = fields.Date('First Approved On', readonly=True)
    director_approve_date = fields.Date('Final Approved On', readonly=True)
    move_id = fields.Many2one('account.move', 'Journal Entry', copy=False)
    journal_id = fields.Many2one('account.journal', 'Journal')
    update_cash = fields.Boolean(string='Update Cash Register?', readonly=False, states={'draft': [(
        'readonly', True)]}, help='Tick if you want to update cash register by creating cash transaction line.')
    cash_id = fields.Many2one('account.bank.statement', string='Cash Register', domain=[('journal_id.type', 'in', [
                              'cash']), ('state', '=', 'open')], required=False, readonly=False, states={'draft': [('readonly', False)]})

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('payment.requisition')
        return super(payment_request, self).create(vals)

    @api.onchange('requester_id')
    def onchange_requester(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self._uid)], limit=1)
        self.employee_id = employee.id
        self.department_id = employee.department_id and employee.department_id.id or False

    def action_confirm(self):
        if not self.request_line:
            raise exceptions.UserError(
                _('Can not confirm request without request lines.'))

        if not self.department_id.manager_id:
            raise exceptions.UserError(
                _('Please contact HR to setup a manager for your department.'))

        if self.amount_company_currency <= self.company_id.min_amount:
            body = _(
                'Payment request %s has been submitted for your approval. Please check and approve.' % (self.name))
            self.notify(body=body, users=[
                        self.department_id.manager_id.user_id.partner_id.id], group=False)
        else:
            self.need_gm_approval = True
            body = _(
                'Payment request %s has been approved by the department Manager. Please provide second approval.' % (self.name))
            self.notify(body=body, users=[],
                        group='ng_payment_request.general_manager')
        self.state = 'awaiting_approval'
        return True

    def action_approve(self):
        for line in self.request_line:
            if line.approved_amount <= 0.0:
                raise exceptions.UserError(
                    _('Approved amount cannot be less then or equal to Zero.'))
                # raise UserError(_('Approved amount cannot be less then or equal to Zero.'))
        # or self.amount_company_currency <= company.max_amount
        # if self.amount_company_currency > self.company_id.min_amount:
        # self.need_gm_approval = True
        self.state = 'mgr_approve'
        body = _(
            'Payment request %s has been approved by admin. Please provide the final approval.' % (self.name))
        self.notify(body=body, users=[],
                    group='ng_payment_request.general_manager')
        # else:
        # self.state = 'approved'
        # body = _('Your request %s has been approved.' % (self.name))
        # self.notify(body=body, users=[
        #             self.employee_id.user_id.partner_id.id])
        body = _(
            'Payment request %s has been approved. Please proceed with the payment.' % (self.name))
        self.notify(body=body, group='account.group_account_manager')
        emp = self.env['hr.employee'].search(
            [('user_id', '=', self._uid)], limit=1)
        self.dept_manager_id = emp.id
        self.dept_manager_approve_date = fields.Date.context_today(self)
        return True

    def action_gm_approve(self):
        for line in self.request_line:
            if line.approved_amount <= 0.0:
                raise exceptions.UserError(
                    _('Approved amount cannot be less then or equal to Zero.'))
        # if self.amount_company_currency > self.company_id.max_amount:
        self.need_md_approval = True
        body = _(
            'Payment request %s has been approved. Please provide final approval.' % (self.name))
        self.notify(
            body=body, group='ng_payment_request.managing_director')
        # else:
        #     self.state = 'approved'
        #     body = _('Your request %s has been approved.' % (self.name))
        #     self.notify(body=body, users=[
        #                 self.employee_id.user_id.partner_id.id])
        #     body = _(
        #         'Payment request %s has been approved. Please proceed with the payment.' % (self.name))
        #     self.notify(body=body, group='account.group_account_manager')
        self.state = 'gm_approve'
        emp = self.env['hr.employee'].search(
            [('user_id', '=', self._uid)], limit=1)
        self.general_manager_id = emp.id
        self.gm_approve_date = fields.Date.context_today(self)
        return True

    def notify(self, body='', users=[], group=False):
        post_msg = []
        if group:
            users = self.env['res.users'].search(
                [('active', '=', True), ('company_id', '=', self.env.user.company_id.id)])
            for user in users:
                if user.has_group(group) and user.id != 1:
                    post_msg.append(user.partner_id.id)
        else:
            post_msg = users
        if len(post_msg):
            self.message_post(body=body, partner_ids=post_msg)
        return True

    def action_md_approve(self):
        emp = self.env['hr.employee'].search(
            [('user_id', '=', self._uid)], limit=1)
        self.manging_director_id = emp.id
        self.state = 'approved'
        self.director_approve_date = fields.Date.context_today(self)
        body = _(
            'Payment request %s has been approved. Please proceed with the payment.' % (self.name))
        self.notify(body=body, group='account.group_account_manager')
        return True

    def action_pay(self):
        move_obj = self.env['account.move']
        # move_line_obj = self.env['account.move.line']
        statement_line_obj = self.env['account.bank.statement.line']

        ctx = dict(self._context or {})
        for record in self:
            company_currency = record.company_id.currency_id
            current_currency = record.currency_id

            ctx.update({'date': record.date})
            sum_line_approved_amount = sum(
                [line.approved_amount for line in record.request_line])

            amount = current_currency.compute(
                sum_line_approved_amount, company_currency)
            if record.journal_id.type == 'purchase':
                sign = 1
            else:
                sign = -1
            asset_name = record.name
            reference = record.name

            move_vals = {
                'date': record.date,
                'ref': reference,
                'currency_id': record.currency_id.id,
                'journal_id': record.journal_id.id,
            }

            journal_id = record.journal_id.id
            partner_id = record.employee_id.address_home_id
            if not partner_id:
                raise exceptions.UserError(
                    _('Please specify Employee Home Address in the Employee Form!.'))

            move_line_vals = []

            L = record.request_line.sorted(
                key=lambda rq: rq.credit_account_id.id)

            def key_func(x): return x['credit_account_id']['name']

            for key, group in groupby(L, key_func):
                for line in list(group):
                    # compute the debit lines
                    amount_line = current_currency.compute(
                        line.approved_amount, company_currency)
                    currency_id = company_currency.id != current_currency.id and current_currency.id or company_currency.id
                    dr_vals = {
                        'name': asset_name,
                        'ref': reference,
                        'account_id': line.expense_account_id.id,
                        'credit': 0.0,
                        'debit': amount_line,
                        'journal_id': journal_id,
                        'partner_id': line.partner_id.id,
                        'customer_id': line.partner_id.id,
                        'currency_id': currency_id,
                        'amount_currency': amount_line,
                        'analytic_distribution': {line.analytic_account_id.id: 100},
                        'date': record.date,
                    }

                    cr_vals = {
                        'name': asset_name,
                        'ref': reference,
                        'account_id': line.credit_account_id.id,
                        'debit': 0.0,
                        'credit': amount_line,
                        'journal_id': journal_id,
                        'partner_id': line.partner_id.id,
                        'customer_id': line.partner_id.id,
                        'currency_id': currency_id,
                        'amount_currency': -1 * amount_line,
                        'date': record.date,
                    }
                    move_line_vals.append(cr_vals)
                    move_line_vals.append(dr_vals)

                key_and_group = {key: list(group)}
                print(key_and_group)

            move_vals.update(line_ids=[(0, 0, line_val)
                             for line_val in move_line_vals])

            move_id = move_obj.with_context(
                check_move_validity=False).create(move_vals)
            record.move_id = move_id.id
            if record.update_cash:
                type = 'general'
                amount = -1 * record.approved_amount
                account = record.journal_id.default_debit_account_id.id
                if not record.journal_id.type == 'cash':
                    raise exceptions.UserError(
                        _('Journal should match with selected cash register journal.'))
                stline_vals = {
                    'name': record.name or '?',
                    'amount': amount,
                    'type': type,
                    'account_id': account,
                    'statement_id': record.cash_id.id,
                    'ref': record.name,
                    'partner_id': partner_id.id,
                    'date': record.date,
                    'payment_request_id': record.id,
                }
                statement_line_obj.create(stline_vals)
        self.state = 'paid'
        return True

    def action_cancel(self):
        self.state = 'cancelled'
        return True

    def action_reset(self):
        self.state = 'draft'
        return True

    def action_refuse(self):
        self.state = 'refused'
        return True

    def payment_method(self, payment_type):
        return self.env["account.payment.method"].search([("code", "=", "manual"), ("payment_type", "=", payment_type)], limit=1)


class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'

    payment_request_id = fields.Many2one(
        'payment.requisition', string='Payment Request')
