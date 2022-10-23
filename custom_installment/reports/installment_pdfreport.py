# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError


class ReportInstallment(models.AbstractModel):
    _name = 'report.custom_installment.report_installment'

    @api.model
    def _get_report_values(self, docids, data=None):
        active_model = self.env.context.get('active_model')
        docs = self.env[active_model].browse(self.env.context.get('active_id'))
        domain = [('customer', '=', docs.customer.id)]
        if docs.date_from:
            domain.append(('date','>=',docs.date_from))
        if docs.date_to:
            domain.append(('date','<=',docs.date_to))

        orders = self.env['installment.installment'].search(domain)


        docargs = {
            'doc_ids': self.ids,
            'doc_model': active_model,
            'docs': docs,
            'installments': orders
        }
        return docargs
