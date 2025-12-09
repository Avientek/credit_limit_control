import frappe
from frappe import _
from frappe.utils import flt

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
    """, customer)[0][0])

    # 3. Open Sales Orders
    open_so = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(grand_total), 0)
        FROM `tabSales Order`
        WHERE docstatus = 1 AND customer = %s AND IFNULL(per_delivered, 0) < 100
    """, customer)[0][0])

    # 4. Open Delivery Notes
    open_dn = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(grand_total), 0)
        FROM `tabDelivery Note`
        WHERE docstatus = 1 AND customer = %s AND IFNULL(per_billed, 0) < 100
    """, customer)[0][0])

    # 5. Unallocated Advances
    advances = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(unallocated_amount), 0)
        FROM `tabPayment Entry`
        WHERE docstatus = 1
        AND party_type='Customer'
        AND payment_type='Receive'
        AND party=%s
        AND IFNULL(unallocated_amount, 0) > 0
    """, customer)[0][0])

    return flt(credit_limit - unpaid_invoices - open_so - open_dn + advances)


def format_currency(val):
    return "{:,.2f}".format(flt(val))


def validate_delivery_note_credit_limit(doc, method=None):
    if not doc.customer:
        return

    available = get_available_credit(doc.customer, doc.company)
    dn_value = flt(doc.grand_total)

    if dn_value > available:
        frappe.throw(
            _("Delivery Note cannot be submitted. Customer credit limit exceeded based on pending invoices, open SO, open DN and advances.")
        )
