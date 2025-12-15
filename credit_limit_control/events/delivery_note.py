import frappe
from frappe import _
from frappe.utils import flt, nowdate


#----------------------------------------------------
# FORMAT CURRENCY
#----------------------------------------------------
def format_currency(val):
    return "{:,.2f}".format(flt(val))


#----------------------------------------------------
# GET AVAILABLE CREDIT LIMIT
#----------------------------------------------------
def get_available_credit(customer, company):
    """Calculate available customer credit."""

    # 1. Credit Limit
    row = frappe.db.sql("""
        SELECT credit_limit
        FROM `tabCustomer Credit Limit`
        WHERE parent = %s AND company = %s
    """, (customer, company), as_dict=True)

    credit_limit = flt(row[0].credit_limit) if row else 0.0
    
    # 2. Unpaid Invoices
    unpaid_invoices = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(outstanding_amount), 0)
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND customer = %s AND outstanding_amount > 0
    """, (customer,))[0][0])

    # 3. Open Sales Orders
    open_so = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(grand_total), 0)
        FROM `tabSales Order`
        WHERE docstatus = 1 AND customer = %s AND IFNULL(per_delivered, 0) < 100
    """, (customer,))[0][0])

    # 4. Open Delivery Notes
    open_dn = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(grand_total), 0)
        FROM `tabDelivery Note`
        WHERE docstatus = 1 AND customer = %s AND IFNULL(per_billed, 0) < 100
    """, (customer,))[0][0])

    # 5. Unallocated Advances
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


#----------------------------------------------------
# OVERDUE LIMIT CHECK
#----------------------------------------------------
def check_overdue_limit(customer, company):
    """Block Delivery Note if customer overdue exceeds allowed limit."""

    # Sum of all overdue outstanding invoices
    overdue_amount = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(outstanding_amount), 0)
        FROM `tabSales Invoice`
        WHERE docstatus = 1
        AND customer = %s
        AND outstanding_amount > 0
        AND due_date < %s
    """, (customer, nowdate()))[0][0])

    # Load customer
    cust = frappe.get_doc("Customer", customer)

    # If no overdue limit defined → skip
    if not cust.overdue_limit:
        return

    # Check child table rows
    for row in cust.overdue_limit:
        if row.company == company:
            if overdue_amount >= flt(row.credit_limit):
                frappe.throw(
                    _(
                        "Delivery Note cannot be submitted.\n\n"
                        "Customer has exceeded the overdue limit.\n"
                        "Overdue Amount: {overdue}\n"
                        "Allowed Limit: {limit}"
                    ).format(
                        overdue=format_currency(overdue_amount),
                        limit=format_currency(row.credit_limit),
                    )
                )


#----------------------------------------------------
# DELIVERY NOTE VALIDATION
#----------------------------------------------------
def validate_delivery_note_credit_limit(doc, method=None):

    if not doc.customer:
        return

    # 1️ CREDIT LIMIT CHECK
    available = get_available_credit(doc.customer, doc.company)
    dn_value = flt(doc.grand_total)

    if dn_value > available:
        frappe.throw(
            _("Delivery Note cannot be submitted. Customer credit limit exceeded based on pending invoices, open SO, open DN and advances.")
        )

    # 2️ OVERDUE LIMIT CHECK
    check_overdue_limit(doc.customer, doc.company)
