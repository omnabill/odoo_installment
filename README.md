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

> 2- Menus

	1- Installments: Main menu (Found Under Customers menu in accounting)
	2- Customer installments: Sub menu under the **Installments** menu 
	3- Reports (Found Under Customers menu in accounting)
	4- installment statement submenu under **Reports**
	

> 3- Views 

	1- Tree
	2- Form
		- Add a tab in the form in which holds a list of all payments that were created. 
	3- Kanban
	4- Search (Search using fields or search pannel)
	
> 4- Buttons

	1- Open installment:
		Creates a customer invoice and generates a sequence for the Name field as it's found in the customer invoice to schedule installments on the customer invoice usig the invoice or can schedule installment freely without invoice from the main menu. 
	2- Payment: (
		Prompt the user with a wizard by which the user can insert a payment of partial amount or full amount of the requested amount.
		Make sure the State is set to "paid" upon reaching the full amount and checks that the installment is fully paid and accept only money that don't exceed the un paid amount.
	3- Settlement:
		Settles the installment with the remaining amount and then set the State to "paid".
		
> 5- Access Rights

	1- User: Has access to self created entries and users can view records without deleting, only user in group can access the module
	2- Manager: Has access to all entries, can delete any records
	
	
> 6- Smart button

	Invoice: Visible only to the Manager group to get the invoice linked with the installment

Notes in model logic: 
	- Delete and edit is only allowed in "draft" State. 
	
> Pivot and Graph view for the installment model.
