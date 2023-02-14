# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockSucursalsirett(models.Model):
    _name = 'stock.sucursal.sirett'
    _inherit = 'mail.thread'
    _description = 'Sucursal sirett Api'
    _rec_name = 'name'
    _order = "id_search asc"

    id_search = fields.Integer(string=u'Identificador para búsqueda', required=True)
    code = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre de sucursal', required=True)
    date_consult = fields.Date(string='Última fecha de consulta', store=True, readonly=True)
    active = fields.Boolean(string="Activo", default=True)
    total_consult = fields.Float(string=u'Número de registros', store=True, readonly=True)
    # warehouse_id = fields.Many2one('Bodega')
    warehouse_id = fields.Many2one('stock.warehouse', 'Bodega Odoo')

    def name_get(self):
        result = []
        for sucursal_sirett in self:
            name = "%s | %s" % (sucursal_sirett.code, sucursal_sirett.name)
            result.append((sucursal_sirett.id, name))
        return result
