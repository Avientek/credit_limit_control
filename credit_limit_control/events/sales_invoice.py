import frappe

def before_submit(doc, method):
    query="""
    SELECT
        si.customer AS customer,
        SUM(si.grand_total) AS grand_total
    FROM
        `tabSales Invoice` AS si
    WHERE
        si.status='Overdue'
    GROUP BY
        si.customer
    """
    amount= frappe.db.sql(f"{query}", as_dict=True)
    customer_overdue_amount = frappe.get_doc('Customer', doc.customer)

    user = frappe.session.user
    role_assigned=frappe.db.get_single_value('Accounts Settings','overdue_controller')
    if customer_overdue_amount.overdue_limit and role_assigned not in frappe.get_roles(user): 
        for i in customer_overdue_amount.overdue_limit:
            if amount[0].grand_total>=i.credit_limit:
                frappe.throw("You cannot Submit due to Overdue Limit")