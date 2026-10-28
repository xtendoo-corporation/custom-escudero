from odoo import fields, models


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    last_autoreply_date = fields.Datetime(
        string="Última respuesta automática de WhatsApp", copy=False
    )
