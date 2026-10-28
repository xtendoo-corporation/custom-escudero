from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    whatsapp_autoreply_enabled = fields.Boolean(
        related="company_id.whatsapp_autoreply_enabled", readonly=False
    )
    whatsapp_autoreply_template_id = fields.Many2one(
        related="company_id.whatsapp_autoreply_template_id", readonly=False
    )
    whatsapp_autoreply_cooldown_hours = fields.Float(
        related="company_id.whatsapp_autoreply_cooldown_hours", readonly=False
    )
