# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,UserError


class ReportWizard(models.TransientModel):
    _name = 'retrieve.pdf.wizard'
    _description = 'Installment Report'

    customer = fields.Many2one(comodel_name='res.partner', string="Customer", required=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    def check_report(self):
        data = {}
        data['form'] = self.read(['customer', 'date_from', 'date_to'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read(['customer', 'date_from', 'date_to'])[0])
        report_action = self.env.ref('custom_installment.report_installments_report').report_action(self, data=data)
        return report_action
