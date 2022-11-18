{
    "name": "L10N CR TOYS SERVICE",
    'summary': """
        Módulo TOYS""",
    'description': """
       1. Sucursales de Toys para consutla.
       2. Api a sucursales Toys para obtener productos.
       3. Derivar stock a almacenes.
    """,
    'version': '14.0.3.3',
    "author": "Jhonny",
    'license': 'LGPL-3',
    "depends": ['base','stock','web_notify'],
    "data": [
        # security
        "security/ir.model.access.csv",
        # data
        "data/stock.sucursal.toys.csv",
        "data/api.params.csv",
        "data/api.params.lines.csv",
        # views
        "view/menus.xml",
        "view/params_api_config_views.xml",
        "view/stock_quant_views.xml",
        "view/stock_sucursal_toys_views.xml",
        "view/product_template_views.xml",
        "wizard/toy_api_wizard.xml",

    ],
}
