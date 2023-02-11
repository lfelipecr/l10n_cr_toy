# -*- coding: utf-8 -*-

from odoo import models, fields


class ApiParams(models.Model):
    _name = 'api.params'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'API | Parámetros'
    _rec_name = 'name'
    _order = "id desc"

    name = fields.Char(string='Nombre', required=True)
    user = fields.Char(string='Usuario', required=True)
    password = fields.Char(string='Clave', required=True)
    cliente = fields.Char(string='Cliente Wsdl', required=True)
    url_base = fields.Char(string='Url Base', required=True)
    api_lines = fields.One2many('api.params.lines', 'api_id', string='Detalles de errores')


class ApiParamsLines(models.Model):
    _name = 'api.params.lines'

    api_id = fields.Many2one('api.params')
    code = fields.Char(string='Código')
    mensaje = fields.Char(string='Mensaje')
