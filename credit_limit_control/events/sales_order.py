import frappe
from frappe.utils import flt

def before_submit(doc, method):

    customer = doc.customer
    user = frappe.session.user
    role_assigned = frappe.db.get_single_value("Accounts Settings", "credit_controller")

    customer_doc = frappe.get_doc("Customer", customer)

    # No credit limit → no validation
    if not customer_doc.credit_limits:
        return

    # Get the credit limit for this company
    credit_limit = 0
    for row in customer_doc.credit_limits:
        if row.company == doc.company:
            credit_limit = flt(row.credit_limit)
            break

    if credit_limit <= 0:
        return

    # Controller can override
    if role_assigned in frappe.get_roles(user):
        return

    # -----------------------------------------
    # 1. OPEN ORDERS (SO submitted, DN not done)
    # -----------------------------------------
    open_orders = frappe.db.sql("""
        SELECT SUM(grand_total)
        FROM `tabSales Order`
        WHERE docstatus = 1
        AND customer = %s
        AND name != %s
    """, (customer, doc.name))[0][0] or 0

    # -----------------------------------------
    # 2. NEW ORDERS (Draft SO)
    # -----------------------------------------
    new_orders = frappe.db.sql("""
        SELECT SUM(grand_total)
        FROM `tabSales Order`
        WHERE docstatus = 0
        AND customer = %s
        AND name != %s
    """, (customer, doc.name))[0][0] or 0

    # -----------------------------------------
    # 3. OPEN DELIVERIES (DN submitted, not billed)
    # -----------------------------------------
    open_deliveries = frappe.db.sql("""
        SELECT SUM(base_grand_total)
        FROM `tabDelivery Note`
        WHERE docstatus = 1
        AND per_billed < 100
        AND customer = %s
    """, customer)[0][0] or 0

    # -----------------------------------------
    # 4. OPEN INVOICES (SI outstanding)
    # -----------------------------------------
    open_invoices = frappe.db.sql("""
        SELECT SUM(outstanding_amount)
        FROM `tabSales Invoice`
        WHERE docstatus = 1
        AND customer = %s
    """, customer)[0][0] or 0

    # -----------------------------------------
    # TOTAL OUTSTANDING
    # -----------------------------------------
    total_outstanding = (
        flt(open_orders)
        + flt(new_orders)
        + flt(open_deliveries)
        + flt(open_invoices)
    )

    # -----------------------------------------
    # VALIDATION
    # -----------------------------------------
    if total_outstanding > credit_limit:
        frappe.throw("You cannot Submit due to Credit Limit")
