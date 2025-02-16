import frappe

def before_submit(doc, method):
    query=frappe.db.sql(f"""
    SELECT
        si.customer AS customer,
        SUM(si.outstanding_amount) AS outstanding_amount
    FROM
        `tabSales Invoice` AS si
    WHERE
        si.status='Overdue' AND si.customer = '{doc.customer}'
    GROUP BY
        si.customer
    """, as_dict = True)

    customer_overdue_amount = frappe.get_doc('Customer', doc.customer)
    user = frappe.session.user
    role_assigned=frappe.db.get_single_value('Accounts Settings','overdue_controller')

    if customer_overdue_amount.overdue_limit and role_assigned not in frappe.get_roles(user): 
        for i in customer_overdue_amount.overdue_limit:
            if query and query[0].outstanding_amount>=i.credit_limit:
                frappe.throw("You cannot Submit due to Overdue Limit")