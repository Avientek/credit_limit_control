import frappe
from frappe import _
from frappe.utils import flt, nowdate

#---------------------------------------------
# FORMAT CURRENCY HELPER
#---------------------------------------------
def format_currency(v):
    return "{:,.2f}".format(flt(v))


#---------------------------------------------
# GET AVAILABLE CREDIT LIMIT
#---------------------------------------------
def get_available_credit(customer, company):
    """Calculate available customer credit."""

    # 1) Credit Limit from Customer Credit Limit table
    row = frappe.db.sql("""
        SELECT credit_limit
        FROM `tabCustomer Credit Limit`
        WHERE parent = %s AND company = %s
    """, (customer, company), as_dict=True)

    credit_limit = flt(row[0].credit_limit) if row else 0.0

    # 2) Unpaid Invoices
    unpaid_invoices = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(outstanding_amount), 0)
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND customer = %s AND outstanding_amount > 0
    """, (customer,))[0][0])

    # 3) Open Sales Orders
    open_so = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(grand_total), 0)
        FROM `tabSales Order`
        WHERE docstatus = 1 AND customer = %s AND IFNULL(per_delivered, 0) < 100
    """, (customer,))[0][0])

    # 4) Open Delivery Notes
    open_dn = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(grand_total), 0)
        FROM `tabDelivery Note`
        WHERE docstatus = 1 AND customer = %s AND IFNULL(per_billed, 0) < 100
    """, (customer,))[0][0])

    # 5) Unallocated Advances
    advances = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(unallocated_amount), 0)
        FROM `tabPayment Entry`
        WHERE docstatus = 1
        AND party_type='Customer'
        AND payment_type='Receive'
        AND party=%s
        AND IFNULL(unallocated_amount, 0) > 0
    """, (customer,))[0][0])

    return flt(credit_limit - unpaid_invoices - open_so - open_dn + advances)


#---------------------------------------------
# OVERDUE LIMIT CHECK
#---------------------------------------------
def check_overdue_limit(customer, company):
    """Check overdue invoices against customer overdue limit."""

    # 1) Overdue amount = outstanding invoices where due_date < today
    overdue_amount = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(outstanding_amount), 0)
        FROM `tabSales Invoice`
        WHERE docstatus = 1
        AND customer = %s
        AND outstanding_amount > 0
        AND due_date < %s
    """, (customer, nowdate()))[0][0])

    # 2) Customer Doctype
    cust = frappe.get_doc("Customer", customer)

    # If no child table records → skip
    if not cust.overdue_limit:
        return

    # 3) Loop child table rows
    for row in cust.overdue_limit:
        if row.company == company:  # match company
            if overdue_amount >= flt(row.credit_limit):
                frappe.throw(
                    _(
                        "Customer has exceeded the overdue limit.\n\n"
                        "Overdue Amount: {overdue}\n"
                        "Allowed Limit: {limit}"
                    ).format(
                        overdue=format_currency(overdue_amount),
                        limit=format_currency(row.credit_limit),
                    )
                )


#---------------------------------------------
# FINAL VALIDATION (CALL BOTH CHECKS)
#---------------------------------------------
def validate_sales_order_credit_limit(doc, method=None):
    if not doc.customer:
        return

    # 1. CREDIT LIMIT CHECK
    available = get_available_credit(doc.customer, doc.company)
    so_value = flt(doc.grand_total or 0)

    if so_value > available:
        frappe.throw(
            _(
                "Sales Order cannot be submitted. "
                "Customer has only {available} available credit limit. "
                "Order value ({value}) exceeds the limit."
            ).format(
                available=format_currency(available),
                value=format_currency(so_value),
            )
        )

    # 2.    OVERDUE LIMIT CHECK
    check_overdue_limit(doc.customer, doc.company)
