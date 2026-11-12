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
    whatsapp_autoreply_mode = fields.Selection(
        related="company_id.whatsapp_autoreply_mode", readonly=False
    )
    whatsapp_autoreply_text = fields.Text(
        related="company_id.whatsapp_autoreply_text", readonly=False
    )
