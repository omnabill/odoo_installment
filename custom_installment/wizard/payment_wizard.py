# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,UserError


class CreatePayment(models.TransientModel):
    _name = 'create.payment.wizard'
    _description = 'Payment Wizard'

    installment_id = fields.Many2one('installment.installment', string='Installment', required=True,readonly=True)
    pay_amount = fields.Float(string='Payment Amount')
    receiver = fields.Many2one('res.users',string='receiver')
    date = fields.Date(string='Payment Date',required=True)
    way = fields.Many2one('account.journal', store=True, readonly=False,
                                 domain="[('type', 'in', ('bank', 'cash'))]",required=True)
    currency_id = fields.Many2one('res.currency',related='installment_id.currency_id')

    @api.constrains('pay_amount')
    def check_payamount(self):
        """Check the amount to ensure that its value is positive value"""
        self.ensure_one()
        for rec in self:
            if rec.pay_amount < 0:
                raise ValidationError("The amount must be a positive value.")

    def action_create_payment(self):
        total_paid = sum(self.installment_id.payment_lines_ids.mapped('amount'))
        if self.installment_id.amount- total_paid == 0:
            raise UserError("The Installment is fully payed you can't add new payments.")
        else:
            if self.pay_amount > self.installment_id.amount- total_paid:
                raise ValidationError("The payment amount is greater than reminded on this installment which is {}".format(self.installment_id.amount- total_paid))
            else:
                vals = {
                'payment_type': 'inbound',
                'amount': self.pay_amount,
                'currency_id':  self.currency_id.id,
                'journal_id': self.way.id,
                'date': self.date,
                'pay_date':self.date,
                'way':self.way.type,
                'partner_id': self.installment_id.customer.id,
                'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
                'partner_type': 'customer',
                'installment_id': self.installment_id.id
            }
                res = self.env['account.payment'].create(vals)
                if self.installment_id.amount- sum(self.installment_id.payment_lines_ids.mapped('amount')) == 0:
                    self.installment_id.action_paid()
                else:
                    self.installment_id.action_open()
                return res


    @api.model
    def default_get(self, fields):
        res = super(CreatePayment, self).default_get(fields)
        if self._context.get('active_id'):
            res['installment_id'] = self._context.get('active_id')
        return res
