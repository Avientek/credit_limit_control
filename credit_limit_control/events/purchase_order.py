import frappe

def before_submit(doc, method):
    query="""
    SELECT
        po.supplier AS supplier,
        SUM(po.grand_total) AS grand_total
    FROM
        `tabPurchase Order` AS po
    WHERE
        po.docstatus=1
    GROUP BY
        po.supplier
    """
    amount= frappe.db.sql(f"{query}", as_dict=True)
    supplier = frappe.get_doc('Supplier', doc.supplier)

    user = frappe.session.user
    role_assigned=frappe.db.get_single_value('Accounts Settings','credit_controller')
    if supplier.credit_limit and role_assigned not in frappe.get_roles(user):
            if amount[0].grand_total>=supplier.credit_limit :
                frappe.throw("You cannot Submit due to Credit Limit")