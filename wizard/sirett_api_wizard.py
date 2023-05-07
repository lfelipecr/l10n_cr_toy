# -*- coding: utf-8 -*-
import logging

from datetime import datetime, date
import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import requests
import threading

OPTIONS = [('data', 'Obtener/Actualizar productos'), ('images', 'Actualizar imágenes'), ('price_stock', 'Actualizar precio y stock')]
result = 6450

_logger = logging.getLogger(__name__)


class StocksirettApiWizard(models.TransientModel):
    _name = 'stock.sirett.api.wizard'
    _description = 'sirett Api - Consulta de productos'

    def _default_api(self):
        return self.env['api.params'].sudo().browse(1)
    
    def _default_location_id(self):
        return self.sucursal_id.warehouse_id.lot_stock_id.id

    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.user.company_id)
    api_id = fields.Many2one('api.params',string='Api credenciales',default=_default_api)
    sucursal_id = fields.Many2one('stock.sucursal.sirett', string=u'Sucursal', required=True)
    location_id = fields.Many2one('stock.location', string=u'Ubicación', store=True, default=_default_location_id)
    description = fields.Text('Respuesta: ', store=True, readonly=True)
    option = fields.Selection(OPTIONS, string='¿Qué desea realizar?', default='data')

    @api.onchange('sucursal_id')
    def _onchange_sucursal_id(self):
        for record in self:
            record.location_id = record.sucursal_id.warehouse_id.lot_stock_id.id

    @staticmethod
    def _create_mensaje(res, sucursal, mensaje):
        mensaje = mensaje + 'A) ' + sucursal.name + ': \n'
        for line in res:
            mensaje = mensaje + '\t\t *' + line + '\n'

        return mensaje

    def update_images(self):
        r = 0
        web_service = self.env['api.webservice'].sudo()
        mensaje = ""
        for sucursal in self.sucursal_id:
            res = web_service.update_images(None, sucursal)
            if isinstance(res, list):
                msn = self._create_mensaje(res,sucursal,mensaje)
                self.description = msn
            else:
                self.description = 'Error al actualizar los productos'
                break
        return {
            'name': 'Webservice sirett',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'stock.sirett.api.wizard',
            'res_id': self.id
        }

    def validate(self):
        if self.location_id and self.sucursal_id:
            sq = self.env['stock.quant'].sudo().search([('sucursal_id', '!=', False), ('sucursal_id', '!=', self.sucursal_id.id), ('location_id', '=', self.location_id.id)])
            if sq:
                raise ValidationError(_("La ubicación seleccionada se está usando para la sucursal "+ str(sq.sucursal_id.name) +" ."))

    def process(self):
        self.validate()
        web_service = self.env['api.webservice'].sudo()
        r = 0
        mensaje = ""
        for sucursal in self.sucursal_id:
            opt = 'new'
            if self.option == 'price_stock':
                opt = 'update_price_stock'

            res = web_service.api_consult_by_sucursal(sucursal, self.api_id, False, opt, self.location_id)
            _logger.info('res: %s' % res)
            if isinstance(res, list):
                msn = self._create_mensaje(res, sucursal, mensaje)
                self.description = msn
                r = -1
            else:
                r = res
                break
        _logger.info('RES: %s' % res)
        if r != -1:
            error = self.api_id.api_lines.filtered(lambda x: x.code == '%s' % r) #error = self.api_id.api_lines.filtered(lambda x: x.code == r.result)
            self.env.user.notify_warning(message=error.mensaje, title="UPS! ")
        else:
            return {
                'name': 'Webservice sirett',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'stock.sirett.api.wizard',
                'res_id': self.id
            }

    def list_view_products(self):
        kanban_id = self.env.ref('product.product_template_kanban_view').id
        list_id = self.env.ref('product.product_template_tree_view').id
        form_id = self.env.ref('product.product_template_only_form_view').id
        return {
            'name': _('Productos'),
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'res_model': 'product.template',
            'domain': [],
            'views': [[kanban_id, "kanban"], [list_id, "tree"], [form_id, "form"]]
        }
