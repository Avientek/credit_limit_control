import frappe

def before_submit(doc, method):
    query=frappe.db.sql(f"""
    SELECT
        so.customer AS customer,
        SUM(so.grand_total) AS grand_total
    FROM
        `tabSales Order` AS so
    WHERE
        so.docstatus = 1 AND so.customer = '{doc.customer}'
    GROUP BY
        so.customer
    """, as_dict = True)

    customer_overdue_amount = frappe.get_doc('Customer', doc.customer)
    user = frappe.session.user
    role_assigned=frappe.db.get_single_value('Accounts Settings','credit_controller')

    if customer_overdue_amount.credit_limits and role_assigned not in frappe.get_roles(user): 
        for i in customer_overdue_amount.credit_limits:
            if query and query[0].grand_total>=i.credit_limit:
                frappe.throw("You cannot Submit due to Credit Limit")