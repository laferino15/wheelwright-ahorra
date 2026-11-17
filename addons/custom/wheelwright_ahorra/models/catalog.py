from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    wah_store_id = fields.Many2one(
        'res.partner', string='Comercio local', domain=[('is_company', '=', True)],
        groups='base.group_user', ondelete='restrict',
    )
    wah_store_name = fields.Char(
        related='wah_store_id.name', string='Nombre público del comercio',
        store=True, compute_sudo=True,
    )
    wah_catalog_sample = fields.Boolean(string='Catálogo ilustrativo / precio de prueba', default=False)
