# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
from datetime import datetime

import requests
from zeep import Client

from odoo import models

# cliente = Client("https://sistema.crgsirett.com/webservice.php?wsdl")
user = '6'
password = 'Pruebas1234*.'
url_base = 'https://sistema.crgsirett.com/'

url = 'https://www.zephysoft.com/webservice.php?wsdl'
headers = {'Content-Type': 'text/xml; charset=utf-8'}

basic_data = """
<ws_pid>{}</ws_pid>
      <ws_passwd>{}</ws_passwd>
      <bid>{}</bid>
      <ws_orden_id>{}</ws_orden_id>
"""

order_items = """
        <ordenitems_Row>
          <codigo>{}</codigo>
          <cantidad>{}</cantidad>
          <precio>{}</precio>
        </ordenitems_Row>
"""

order_client = """
<cliente xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="ns0:clientes_Row">
        <idtipo>{}</idtipo>
        <identificacion>{}</identificacion>
        <nombre>{}</nombre>
        <email>{}</email>
        <phone>{}</phone>
        <fe_email></fe_email>
        <provincia>{}</provincia>
        <ciudad>{}</ciudad>
        <distrito>{}</distrito>
        <direccion>{}</direccion>
</cliente>
"""

body = """
<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
  <soap-env:Body>
    <ns0:wsp_send_orden xmlns:ns0="urn:server">
      {}
      {}
      <detalle xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="ns0:ordenitems_Table"  arrayType="tns:ordenitems_Row[{}]">
        {}  
      </detalle>
    </ns0:wsp_send_orden>
  </soap-env:Body>
</soap-env:Envelope>
"""

errors = {
    '1':'Cuenta de Consulta no existe en el Sistema.',
    '2':'Cuenta sin Acceso al Webservice.',
    '3':'Contraseña incorrecta.',
    '4':'No tiene permiso para utilizar la consulta.',
    '5':'Plataforma SiReTT no tiene la licencia habilitada.',
    '6':'Artículo no encontrado (aplica para consultas específicas de un producto).',
    '7':'No se recibió el número de orden (ws_orden_id)',
    '8':'Orden ya fue procesada en el Sistema SiReTT.',
    '9':'No se ha encontrado la Bodega indicada en el sistema, o no tienes permiso para realizar ordenes en la misma.',
    '1':'Faltan datos estrictos del cliente (nombre, email, teléfono)',
    '11':'Datos incorrectos recibidos en el Tipo y Número de Cédula/Identificación del cliente (de acuerdo al Ministerio de Hacienda)',
    '12':'Formato inválido en direcciones de Correo.',
    '13':'No hay contenido para procesar la Orden.',
    '14':'No se definió correctamente el detalle de la línea de artículo para la orden.',
    '15':'Artículo no encontrado en el sistema (para ordenes y pre-ventas)',
    '16':'Cantidad no válida de acuerdo a la configuración del artículo.',
    '17':'Errores detectados en líneas de detalle recibidas para la orden.',
    '18':'No hay stock en la línea de detalle para reservar la mercadería',
    '19':'Algunos artículos del detalle no tienen stock para reservar la mercadería.',
}


class SirettApiConsult(models.TransientModel):
    _name = 'sirett.api.consult'
    _description = 'Sirett Api - Consulta'

    def get_result(self,id_search):
        r = cliente.service.wsp_request_bodega_all_items(user, password, id_search)
        if r.result==0:
            print(r)
            return r
        else:
            self.env.user.notify_warning(message=errors[r.result], title="UPS! ")

    def _new(self, data):
        product_t = self.env['product.template']
        for product in data:
            p_odoo = product_t.search([('default_code', '=', product.codigo)])
            data = {
                'name': product.descripcion,
                'default_code': product.codigo,
                'stock_actual_sirett': product.stock or 0.0,
                'list_price': product.precio,
                'date_consult': datetime.now().date(),
                'presentation': product.presentacion,
                'marca': product.marca,
                'familia': product.familia,
                'url_image': url_base + '' + product.image_url if product.image_url else product.image_url,
                #'sucursal_id': sucursal.id
            }
            if p_odoo:
                p_odoo.write(data)
            else:
                product_t.create(data)

    def api_consult_by_sucursal(self, sucursal_id, product_id, type):
        product_t = self.env['product.template']
        for sucursal in sucursal_id:
            r = self.get_result(str(sucursal.id_search))
            data = r.data
            sucursal_id.write({'date_consult': datetime.now().date(), 'total_consult': len(r.data)})
            if product_id and (type=='image' or type=='stock'):
                product = list(filter(lambda x: x.codigo == product_id.default_code, data))[0]
                if product:
                    img_b64 = False
                    if product.image_url != None:
                        response_image = requests.get(url_base + '' + product.image_url)
                        if response_image:
                            img_bytes = response_image.content
                            img_b64 = base64.b64encode(img_bytes)

                    if img_b64:
                        image_1920 = img_b64
                        url_image = url_base + '' + product.image_url
                    else:
                        image_1920 = None
                        url_image = None
                    data = {
                        'name': product.descripcion,
                        'default_code': product.codigo,
                        'stock_actual_sirett': product.stock or 0.0,
                        'list_price': product.precio,
                        'date_consult': datetime.now().date(),
                        'presentation': product.presentacion,
                        'marca': product.marca,
                        'familia': product.familia,
                        'url_image': url_image,
                        'sucursal_id': sucursal.id,
                        'image_1920': image_1920,
                    }
                    product_id.write(data)
                    return True
                else:
                    return False
                # self.env.user.notify_success(
                #     message='Los datos del producto fueron actualizdos correctamente. ',
                #     title="BIEN! ")

            else:

                for product in data:
                    p_odoo = product_t.search([('default_code', '=', product.codigo)])
                    data = {
                        'name': product.descripcion,
                        'default_code': product.codigo,
                        'stock_actual_sirett': product.stock or 0.0,
                        'list_price': product.precio,
                        'date_consult': datetime.now().date(),
                        'presentation': product.presentacion,
                        'marca': product.marca,
                        'familia': product.familia,
                        'url_image': url_base + '' + product.image_url if product.image_url else product.image_url,
                        'sucursal_id': sucursal.id
                    }

                    if p_odoo:
                        p_odoo.write(data)
                    else:
                        product_t.create(data)

                return True
