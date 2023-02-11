# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_actual_sirett = fields.Float(string=u'Último stock obtenido')
    date_consult = fields.Date('Consultado el: ')
    presentation = fields.Char(string=u'Presentación')
    marca = fields.Char(string='Marca')
    familia = fields.Char(string='Familia')
    url_image = fields.Char(string='Imagen Url')
    sucursal_id = fields.Many2one('stock.sucursal.sirett', store=True,string=u'Última sucursal obtenida')
    locacion_id = fields.Many2one('stock.location', string=u'Última ubicación obtenida', store=True)


    # def consult_stock_sirett(self):
    #     sirett_api_consult = self.env['sirett.api.consult']
    #     for product in self:
    #         sirett_api_consult.api_consult_by_sucursal(product.sucursal_id, product, 'stock')
    #
    #     self.env.user.notify_success(
    #         message='Los datos del producto fueron actualizdos correctamente. ',
    #         title="BIEN! ")

    def update_image_sirett(self):
        webservice = self.env['api.webservice'].sudo()
        sw = 0
        for product in self:
            r = webservice.update_images(product, None)
            if r == 0:
                break

        if sw == 1:
            self.env.user.notify_warning(message='No se encontró el producto. ', title = "Ups! ")
        else:
            self.env.user.notify_success(message='Los datos del producto fueron actualizdos correctamente. ',title="BIEN! ")





