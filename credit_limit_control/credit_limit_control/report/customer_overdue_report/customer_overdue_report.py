# Copyright (c) 2022, avientek and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{
			'fieldname': 'customer',
			'label': _('Customer'),
			'fieldtype': 'Data',
			'width': 150
		},
		{
			'fieldname': 'credit_limit',
			'label': _('Credit Limit'),
			'fieldtype': 'Currency',
			'width': 150
		},
		{
			'fieldname': 'overdue_limit',
			'label': _('Overdue Limit'),
			'fieldtype': 'Currency',
			'width': 150
		},
		{
			'fieldname': 'grand_total',
			'label': _('Total Outstanding'),
			'fieldtype': 'Currency',
			'width': 150
		},
		{
			'fieldname': 'overdue',
			'label': _('Overdue'),
			'fieldtype': 'Currency',
			'width': 150
		},
		{
			'fieldname': 'credit_balance',
			'label': _('Credit Blance'),
			'fieldtype': 'Currency',
			'width': 150
		},
		{
			'fieldname': 'overdue_balance',
			'label': _('Overdue Balance'),
			'fieldtype': 'Currency',
			'width': 150
		}
	]
	return columns

def get_data(filters):
	query = f'''
			SELECT
				cus.customer_name AS customer,
				ccl.credit_limit AS credit_limit,
				ol.credit_limit AS overdue_limit,
				SUM(si.grand_total) AS overdue,
				so.grand_total as grand_total,
				(ol.credit_limit-SUM(si.grand_total)) AS overdue_balance,
				(ccl.credit_limit-so.grand_total) AS credit_balance
			FROM
				`tabCustomer` AS cus LEFT JOIN
				`tabCustomer Credit Limit` AS ccl ON ccl.parent=cus.name LEFT JOIN
				`tabOverdue Limit` AS ol ON ol.parent=cus.name LEFT JOIN
				`tabSales Invoice` AS si ON si.customer=cus.name LEFT JOIN
				(
				SELECT
					so.customer AS customer,
					SUM(so.grand_total) AS grand_total
				FROM
					`tabSales Order` AS so
				WHERE
					so.docstatus = 1
				GROUP BY
					so.customer
				) AS so ON so.customer = cus.name
			WHERE
				si.status='Overdue'
		'''
	if filters.customer:
		query = f"{query} AND cus.customer_name='{filters.customer}'"
	query = f"{query} GROUP BY si.customer"
		
	data= frappe.db.sql(f"{query}", as_dict=True)
	return data