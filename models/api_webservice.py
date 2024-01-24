# -*- coding: utf-8 -*-
import base64
from datetime import datetime

import requests
import re
from lxml import etree
from pytz import timezone
from zeep import Client

from datetime import date
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
        resultado = cliente.service.wsp_request_bodega_items(int(api_id.user), api_id.password, id_search)
        cliente.create_message(cliente.service, 'wsp_request_bodega_items', api_id.user, api_id.password, id_search)
        return resultado

    #@staticmethod
    def _prepare_product_data(self, product):
        ret_product = {
                'name': product.descripcion,
                'default_code': product.codigo,
                'stock_actual_sirett': product.stock or 0.0,
                'list_price': product.precio,
                'date_consult': datetime.now().date(),
                'presentation': product.presentacion,
                'marca': product.marca,
                'familia': product.familia,
                'type': 'product',
            }
        existe_barcode = self.env["product.template"].search([('barcode', '=', product.codigo)])
        if len(existe_barcode) > 0:
            ret_product['barcode'] = product.codigo
        return ret_product

    def _new(self, datos, api_id, sucursal, location_id, stock_inventory_id):
        product_t = self.env['product.template']
        info = []
        update = 0
        ids_not_update = []
        for product in datos:
            product_template = product_t.search([('default_code', '=', product.codigo)])
            if product_template:
                product_template.write({'locacion_id': location_id.id})
                update += 1
                self.create_stock_move(product_template, product.stock, location_id, sucursal, stock_inventory_id)
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
                self.create_stock_move(p, p.stock_actual_sirett, location_id, sucursal, stock_inventory_id)

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

    def update_pricestock(self, datos, api_id, sucursal, stock_inventory_id):
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
                self.create_stock_move(p_odoo, product.stock, p_odoo.locacion_id,sucursal,stock_inventory_id)

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
        stock_inventory_id = self.env['stock.inventory'].create({
            'location_ids': [(6,0,[location_id.id])],
            'name': 'Ajuste de inventario '+str(date.today()),
            'accounting_date': date.today(),
            'exhausted': True,
            'prefill_counted_quantity': 'zero',
        })

        r = self.get_result(str(sucursal_id.id_search), api_id)
        if r.result != 0:
            result = r.result
        else:
            data = r.data
            if type == 'new':
                result = self._new(data, api_id, sucursal_id, location_id, stock_inventory_id)
            elif type == 'update_price_stock':
                result = self.update_pricestock(data, api_id, sucursal_id, stock_inventory_id)

        if len(stock_inventory_id.line_ids) > 0:
            stock_inventory_id.action_start()
            stock_inventory_id.action_validate()
        else:
            stock_inventory_id.unlink()

        return result


    def update_images(self, product_id, sucursal_id):
        if sucursal_id:
            products = self.env['product.template'].search([('sucursal_id', '=', sucursal_id.id), ('url_image', '!=', False),("image_1920","=",False)],limit=2000)
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
        if product.url_image.split('.com')[1][0] != '/':
            url_split = product.url_image.split('.com')
            url = url_split[0] + '.com/' + url_split[1]
        else:
            url = product.url_image
        response_image = requests.get(url)
        if response_image.status_code == 200:
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

    def create_stock_move(self, product, qty, location_id, sucursal, stock_inventory_id):
        if stock_inventory_id:
            stock_inventory_line_id = self.env['stock.inventory.line'].create({
                'inventory_id': stock_inventory_id.id,
                'product_id': product.product_variant_id.id,
                'product_qty': qty,
                'location_id': location_id.id,
            })

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
            partner_id.identification_id.code_sirett,
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
        sucursal_sirett = self.env['stock.sucursal.sirett'].search([('warehouse_id', '=', order_id.warehouse_id.id),("active","=",True)],limit=1)
        if sucursal_sirett:
            warehouse_number = sucursal_sirett.id_search
        else:
            raise ValidationError("Es necesario indicar el almacén de la orden y que exista una sucursal relacionada a dicho almacén para poder enviar la venta a Sirett.")
        client = self._prepare_client_zirett(api_id, order_id)
        detalle = self._prerare_line_order_zirett(api_id, order_id)
        order_number = re.search(r'\d+', self.name)
        order_number = int(order_number.group())
        credential = basic_data.format(api_id.user, api_id.password, str(warehouse_number), order_number)
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
