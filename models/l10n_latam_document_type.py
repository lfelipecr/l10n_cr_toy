from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'l10n_latam.document.type'

    code_sirett = fields.Integer()
