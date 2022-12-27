import frappe

def before_submit(doc, method):
    query="""   
    SELECT
        SUM(pi.grand_total) AS grand_total,
        pii.purchase_order AS purchase_order
    FROM
        `tabPurchase Invoice` AS pi LEFT JOIN
        `tabPurchase Invoice Item` AS pii ON pii.parent=pi.name

    WHERE
        pi.docstatus=1 AND pii.purchase_order IS NULL
    GROUP BY
        pi.supplier,pii.purchase_order
        """
    amount= frappe.db.sql(f"{query}", as_dict=True)
    supplier = frappe.get_doc('Supplier', doc.supplier)

    user = frappe.session.user
    role_assigned=frappe.db.get_single_value('Accounts Settings','overdue_controller')
    if supplier.billing_limit and role_assigned not in frappe.get_roles(user):
            if amount[0].grand_total>=supplier.billing_limit :
                frappe.throw("You cannot Submit due to Billing Limit")
    