# odoo_installment
           ## Installment Full App in odoo 
           
> 1- Model (Have The Following Fields)
	- Name: installment.installment 
	- Fields:
		1- Name: Char. Readonly
		2- Reference: Char
		3- State: Selection = (draft, open , paid)
		4- Date: Date. Default = today
		5- Customer: Many2one. Required
		6- Journal: Many2one. Required
		7- Account: Many2one. Required
		8- Analytic account: Many2one
		9- Analytic tags: Many2many
		10- Amount: Float. Required, positive
		11- Notes: Text
