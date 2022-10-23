from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import json
from lxml import etree


class Installment(models.Model):
    _name = "installment.installment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Installment"
    # _order = "name desc"
    _rec_name = "name"

    name = fields.Char(string='Name', required=True, copy=False,
                       readonly=True, default=lambda self: _('Draft'))
    reference = fields.Char(string='Reference')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('paid', 'Paid')], string='State', default='draft',
                             tracking=True)
    date = fields.Date(string='Date', default=fields.Date.today)
    customer = fields.Many2one(comodel_name='res.partner', string="Customer", required=True)
    journal = fields.Many2one(comodel_name='account.journal', string='Journals', required=True)
    account = fields.Many2one(comodel_name='account.account', string='Account', required=True)
    analytic_account = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account')
    analytic_tags = fields.Many2many(comodel_name='account.account.tag', string='Account Tags')
    amount = fields.Float(string="Amount", required=True)
    notes = fields.Text(string="Notes")
    invoice_count = fields.Integer(compute='get_total_invoices')
    payment_lines_ids = fields.One2many('account.payment', 'installment_id',
                                        string="Payment Lines", copy=True,
                                        auto_join=True)
    currency_id = fields.Many2one('res.currency', related='customer.property_product_pricelist.currency_id')
    invoice_id = fields.Many2one('account.move', help="The Invoice Linked to the installment")

    @api.constrains('amount')
    def check_amount(self):
        """Check the amount to ensure that its value is positive value"""
        self.ensure_one()
        for rec in self:
            if rec.amount < 0:
                raise ValidationError("The amount must be a positive value.")

    def unlink(self):
        """to override the action of deleting a record
           only (draft) can be deleted raise error when trying to delete for other states"""
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("You can only delete installments with Draft state.")
            else:
                if rec.payment_lines_ids:
                    raise UserError(_("There are payments referring to this record you should delete them first."))
                else:
                    return super(Installment, self).unlink()

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_open(self):
        for rec in self:
            rec.state = 'open'

    def action_paid(self):
        for rec in self:
            if rec.amount - sum(rec.payment_lines_ids.mapped('amount')) != 0:
                raise UserError("You must settle the installment first and it will automatically be in paid status.")
            else:
                rec.state = 'paid'

    def get_total_invoices(self):
        for rec in self:
            rec.invoice_count = self.env['account.move'].search_count(
                [('id', '=', rec.invoice_id.id)])  # get the right search values

    def action_view_invoice(self):
        for rec in self:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            return {
                'name': _('Invoices'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'domain': [],
                'view_mode': 'form',
                'views': form_view,
                'view_id': self.env.ref('account.view_move_form').id,
                'target': 'current',
                'res_id': self.env['account.move'].search([('id', '=', rec.invoice_id.id)]).id
            }

    def settle_installment_payment(self):
        for rec in self:
            paid_amount = sum(rec.payment_lines_ids.mapped('amount'))
            if paid_amount >= rec.amount:
                raise UserError("The Installment is fully payed no thing to settle.")
            vals = {
                'payment_type': 'inbound',
                'amount': rec.amount - paid_amount,
                'currency_id': self.env.user.company_id.currency_id.id,
                'date': datetime.today(),
                'pay_date': datetime.today(),
                'way': 'cash/bank',
                'partner_id': self.customer.id,
                'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
                'partner_type': 'customer',
                'installment_id': rec.id
            }
            res = self.env['account.payment'].create(vals)
            if rec.amount - sum(rec.payment_lines_ids.mapped('amount')) == 0:
                rec.state = 'paid'
                return res

    @api.model
    def default_get(self, fields):
        res = super(Installment, self).default_get(fields)
        if self._context.get('active_model'):
            res['invoice_id'] = self._context.get('invoice_id')
            res['customer'] = self._context.get('customer')
        return res

    @api.model
    def create(self, vals):

        if vals.get('name', _('Draft')) == _('Draft'):  # get next sequence
            vals['name'] = self.env['ir.sequence'].next_by_code('installment.installment') or _('New')

            if vals.get('invoice_id'):
                total_invoice_amount = self.env['account.move'].search([('id', '=', vals['invoice_id'])]).amount_total
                # print(total_invoice_amount)
                past_installment_total = sum(
                    self.env['installment.installment'].search([('invoice_id', '=', vals['invoice_id'])]).mapped(
                        'amount'))
                # print(past_installment_total + vals['amount'],total_invoice_amount)
                if past_installment_total + vals['amount'] > total_invoice_amount:
                    raise UserError(_(
                        "The amount entered in the installment is greater than the reminded amount need to be entered which is {}".format(
                            total_invoice_amount - past_installment_total)))
                else:

                    res = super(Installment, self).create(vals)
                    return res
            else:
                res = super(Installment, self).create(vals)
                return res


class InstallmentPayment(models.Model):
    _inherit = 'account.payment'
    _description = "Payment lines"
    # _order = "name desc"
    # _rec_name = "reference"

    installment_id = fields.Many2one('installment.installment', string='Installment')
    pay_date = fields.Date(string="Payment Date")
    way = fields.Char()


class InvoiceInstallments(models.Model):
    _inherit = 'account.move'
    _description = 'Installment Invoice'

    installment_ids = fields.One2many('installment.installment', 'invoice_id',
                                      string="Installments Linked", copy=True,
                                      auto_join=True)
    count_installments = fields.Integer(compute='_get_count_installments')

    def action_create_installment(self):
        for rec in self:
            total_amount_payment = sum(rec.installment_ids.mapped('amount'))
            if total_amount_payment >= rec.amount_total:
                raise UserError(_("All the invoice installments has been already created."))
                return
            else:
                try:
                    form_view_id = self.env.ref("custom_installment.view_installment_form").id
                except Exception as e:
                    form_view_id = False
                self.env.context = dict(self.env.context)
                self.env.context.update({
                    'invoice_id': rec.id,
                    'customer': rec.partner_id.id,
                })
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Installment Form View',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'installment.installment',
                    'views': [(form_view_id, 'form')],
                    'target': 'current',
                    'context': self.env.context,
                }

    def _get_count_installments(self):
        for rec in self:
            rec.count_installments = self.env['installment.installment'].search_count([('invoice_id', '=', rec.id)])

    def action_view_installments(self):
        for rec in self:
            return {
                'name': _('Installments'),
                'type': 'ir.actions.act_window',
                'res_model': 'installment.installment',
                'domain': [('invoice_id', '=', rec.id)],
                'view_mode': 'tree,form',
                'target': 'current',
            }
