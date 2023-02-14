# -*- coding: utf-8 -*-
import base64
from datetime import datetime

import requests
from lxml import etree
from pytz import timezone
from zeep import Client

from odoo import models, fields
from odoo.exceptions import ValidationError
from .consult_api_sirett import basic_data
from .consult_api_sirett import body
from .consult_api_sirett import order_client
from .consult_api_sirett import order_items
from .zirett_message import zirett_message as MESSAGE

zone = timezone('America/Lima')


class ApiWebservice(models.TransientModel):
    _name = 'api.webservice'
    _description = 'Api Webservice - Consulta'

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    @staticmethod
    def get_result(id_search, api_id):
        cliente = Client(api_id.cliente)
        print('api_id.cliente:{} - api_id.user:{} - api_id.password:{} - id_search:{}'.format(api_id.cliente, api_id.user, api_id.password, id_search))
        r = cliente.service.wsp_request_bodega_all_items(api_id.user, api_id.password, id_search)
        cliente.create_message(cliente.service, 'wsp_request_bodega_all_items', api_id.user, api_id.password, id_search)
        return r

    @staticmethod
    def _prepare_product_data(product):
        return {
            'name': product.descripcion,
            'default_code': product.codigo,
            'barcode': product.codigo,
            'stock_actual_sirett': product.stock or 0.0,
            'list_price': product.precio,
            'date_consult': datetime.now().date(),
            'presentation': product.presentacion,
            'marca': product.marca,
            'familia': product.familia,
            'type': 'product',
        }

    def _new(self, datos, api_id, sucursal, location_id):
        product_t = self.env['product.template']
        info = []
        update = 0
        ids_not_update = []
        for product in datos:
            product_template = product_t.search([('default_code', '=', product.codigo)])
            if product_template:
                product_template.write({'locacion_id': location_id.id})
                update += 1
                self.create_stock_move(product_template, product.stock, location_id, sucursal)
                continue
            data = self._prepare_product_data(product)
            # additionals
            data.update(
                url_image=api_id.url_base + '' + product.image_url if product.image_url else product.image_url,
                sucursal_id=sucursal.id,
                locacion_id=location_id.id
            )
            info.append(data)
        num_lotes, all_p = self.procedure_lotes(info, update)
        if len(all_p) > 0:
            for p in all_p[0]:
                self.create_stock_move(p, p.stock_actual_sirett, location_id, sucursal)

        actualizaciones = update
        nuevos = len(info)
        total = len(datos)
        num_lotes = num_lotes

        #a retornar
        result = []
        result.append('Lotes procesados: ' + str(num_lotes))
        result.append('Nuevos: ' + str(nuevos))
        result.append('Actualizados: ' + str(actualizaciones))
        #result.append('Encontrados/No actualizados: ' + str(len(ids_not_update)))
        result.append('Movimientos creados/actualizados: ' + str(total))
        result.append('Total: ' + str(total))
        return result

    def update_pricestock(self, datos, api_id, sucursal):
        product_t = self.env['product.template']
        info = []
        update = 0
        create = 0
        ids_not_update = []
        for product in datos:
            p_odoo = product_t.search([('default_code', '=', product.codigo), ('active', '=', True)])
            data = {
                'default_code': product.codigo,
                'stock_actual_sirett': product.stock or 0.0,
                'list_price': product.precio or 0.0,
                'date_consult': datetime.now().date(),
            }
            if not p_odoo:
                create += 1
            else:
                p_odoo.write(data)
                update += 1
                self.create_stock_move(p_odoo, product.stock, p_odoo.locacion_id,sucursal)


        actualizaciones = update
        total = len(datos)

        #a retornar
        result = []
        result.append('No encontrados: ' + str(create))
        result.append('Actualizados: ' + str(actualizaciones))
        result.append('Movimientos actualizados: ' + str(update))
        result.append('Total: ' + str(total))
        return result

    def procedure_lotes(self, info, update):
        product_t = self.env['product.template']
        initial, end, part_lote = self.params()
        t = len(info)+update
        div = t / part_lote
        part = int(div) + 1 if div > int(div) else int(div)
        all_p = []
        for i in range(0, part):
            if len(info) > 0:
                all_p.append(product_t.create(info[initial:end]))
            initial = initial + part_lote
            end = end + part_lote
        return part, all_p

    def api_consult_by_sucursal(self, sucursal_id, api_id, product_id, type, location_id):
        for sucursal in sucursal_id:
            r = self.get_result(str(sucursal.id_search), api_id)
            if r.result != 0:
                return r.result
            else:
                data = r.data
                if type == 'new':
                    r = self._new(data, api_id, sucursal, location_id)
                elif type == 'update_price_stock':
                    r = self.update_pricestock(data, api_id, sucursal)
                return r

    def update_images(self, product_id, sucursal_id):
        if sucursal_id:
            products = self.env['product.template'].search([('sucursal_id', '=', sucursal_id.id), ('url_image', '!=', False)])
        else:
            products = self.env['product.template'].search([('id', '=', product_id.id), ('url_image', '!=', False)])
        initial, end, part_lote = self.params()
        t = len(products)
        div = t / part_lote
        part = int(div) + 1 if div > int(div) else int(div)

        for i in range(0,part):
            for product in products[initial:end]:
                image_1920 = self.get_img(product)
                product.image_1920 = image_1920
            initial = initial + part_lote
            end = end + part_lote
        result = []
        result.append('Actualizados: ' + str(t))
        result.append('Lotes procesados: ' + str(part))
        return result

    def get_img(self,product):
        response_image = requests.get(product.url_image)
        if response_image.status_code==200:
            img_bytes = response_image.content
            img_b64 = base64.b64encode(img_bytes)
            if img_b64:
                   return img_b64
            else:
                return False
        else:
            return False

    def params(self):
        initial = 0
        end = 1000
        part_lote = 1000
        return initial, end, part_lote

    def create_stock_move(self, product, qty, location_id, sucursal):
        stock = self.env['stock.quant'].sudo().search([('product_id', '=', product.product_variant_id.id),('sucursal_id','=',sucursal.id)])
        if stock:
            for s in stock:
                if s.location_id.id == location_id.id:
                    s.write({'quantity': qty,
                            'inventory_quantity': qty,
                            'reserved_quantity': 0
                             })
        else:
            quant_vals = {
                'product_id': product.product_variant_id.id,
                'product_uom_id': product.product_variant_id.uom_id.id,
                'location_id': location_id.id,
                'quantity': qty,
                'inventory_quantity': qty,
                'reserved_quantity': 0,
                'sucursal_id': sucursal.id
            }
            self.env['stock.quant'].sudo().create(quant_vals)

    @staticmethod
    def _prerare_line_order_zirett(api_id, order_id):
        items = """"""
        for line in order_id.order_line:
            items += order_items.format(line.product_id.default_code, line.product_uom_qty, line.price_unit)
        return items

    @staticmethod
    def _prepare_client_zirett(api_id, order_id):
        partner_id = order_id.partner_id
        direccion = order_id.partner_id.street or ''
        direccion += order_id.partner_id.street2 or ''
        return order_client.format(
            partner_id.p2p_document_type.code_sirett,
            partner_id.vat,
            partner_id.name,
            partner_id.email,
            partner_id.phone,
            '',
            partner_id.state_id.code,
            partner_id.county_id.code,
            partner_id.district_id.code,
            direccion
        )

    def _check_execption_zirett(self, api_id, results):
        root = etree.fromstring(results.encode())
        results = root.findall(".//result")
        message = MESSAGE[results[0].text]
        for codigo, mensaje in zip(root.findall(".//codigo"), root.findall(".//reply")):
            if mensaje.text == '0':
                continue
            if mensaje.text == '15':
                message += '\n -{} codigo: {}'.format(MESSAGE[mensaje.text], codigo.text)
                continue
            message += '\n -{}'.format(MESSAGE[mensaje.text])
        if message:
            raise ValidationError(message)

    def _post_order(self, order_id):
        api_id = self.env['api.params'].search([], limit=1)
        sucursal_sirett = self.env['stock.sucursal.sirett'].search([('warehouse_id', '=', order_id.warehouse_id.id)])
        client = self._prepare_client_zirett(api_id, order_id)
        detalle = self._prerare_line_order_zirett(api_id, order_id)
        print(detalle)
        credential = basic_data.format(api_id.user, api_id.password, str(sucursal_sirett.id_search), order_id.id)
        data = body.format(credential, client, len(order_id.order_line), detalle)
        headers = {'Content-Type':'text/xml; charset=utf-8'}
        response = requests.post(api_id.cliente, headers=headers, data=data)
        client = Client(wsdl=api_id.cliente)
        root = etree.fromstring(response.text.encode())
        if root.find(".//result").text == '0':
            order_id.send_sirett = True
            order_id.message_post(body='El pedido fue enviado a la sirett')
        else:
            self._check_execption_zirett(api_id, response.text)
