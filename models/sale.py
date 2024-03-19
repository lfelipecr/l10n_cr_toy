from odoo import api, fields, models


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	send_sirett = fields.Boolean('Enviado a sirett', default=False, copy=False)

	def send_order_sirett(self):
		self.env['api.webservice']._post_order(self)
		return True
