# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockSucursalToys(models.Model):
    _name = 'stock.sucursal.toys'
    _inherit = 'mail.thread'
    _description = 'Sucursal Toys Api'
    _rec_name = 'name'
    _order = "id_search asc"

    id_search = fields.Integer(string=u'Identificador para búsqueda', required=True)
    code = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre de sucursal', required=True)
    date_consult = fields.Date(string='Última fecha de consulta', store=True, readonly=True)
    active = fields.Boolean(string="Activo", default=True)
    total_consult = fields.Float(string=u'Número de registros', store=True, readonly=True)



    def name_get(self):
        result = []
        for sucursal_toy in self:
            name = "%s | %s" % (sucursal_toy.code, sucursal_toy.name)
            result.append((sucursal_toy.id, name))
        return result


