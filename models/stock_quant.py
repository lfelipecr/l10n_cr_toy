# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    sucursal_id = fields.Many2one('stock.sucursal.sirett', store=True, string='Sucursal', copy=False)
