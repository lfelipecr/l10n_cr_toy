{
    'name': 'L10N CR Sirett SERVICE',
    'summary': '''
        Módulo Sirett''',
    'description': '''
       1. Sucursales de Sirett para consutla.
       2. Api a sucursales Sirett para obtener productos.
       3. Derivar stock a almacenes.
    ''',
    'version': '14.0.5.3',
    'author': 'Jhonny',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'stock',
        'sale',
        'web_notify',
        'l10n_latam_invoice_document',
        'place2pay'
    ],
    'data': [
        'security/ir.model.access.csv',
        'view/menus.xml',
        'view/params_api_config_views.xml',
        'view/stock_quant_views.xml',
        'view/stock_sucursal_sirett_views.xml',
        'view/product_template_views.xml',
        'view/sale.xml',
        'view/document_type.xml',
        'wizard/sirett_api_wizard.xml',
        'data/api.params.csv',
        'data/stock.sucursal.sirett.csv',
        'data/api.params.lines.csv',
        'data/update_document_type.xml'
    ],
}
