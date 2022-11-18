# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_actual_toys = fields.Float(string=u'Último stock obtenido')
    date_consult = fields.Date('Consultado el: ')
    presentation = fields.Char(string=u'Presentación')
    marca = fields.Char(string='Marca')
    familia = fields.Char(string='Familia')
    url_image = fields.Char(string='Imagen Url')
    sucursal_id = fields.Many2one('stock.sucursal.toys', store=True,string=u'Última sucursal obtenida')
    locacion_id = fields.Many2one('stock.location', string=u'Última ubicación obtenida', store=True)


    # def consult_stock_toys(self):
    #     toys_api_consult = self.env['toys.api.consult']
    #     for product in self:
    #         toys_api_consult.api_consult_by_sucursal(product.sucursal_id, product, 'stock')
    #
    #     self.env.user.notify_success(
    #         message='Los datos del producto fueron actualizdos correctamente. ',
    #         title="BIEN! ")

    def update_image_toy(self):
        webservice = self.env['api.webservice'].sudo()
        sw=0
        for product in self:
            r = webservice.update_images(product,None)
            if r==0:
                sw==1
                break

        if sw==1:
            self.env.user.notify_warning(message='No se encontró el producto. ', title = "Ups! ")
        else:
            self.env.user.notify_success(message='Los datos del producto fueron actualizdos correctamente. ',title="BIEN! ")





