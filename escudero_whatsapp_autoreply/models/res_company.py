from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    whatsapp_autoreply_enabled = fields.Boolean(
        string="Respuesta automática de WhatsApp",
    )
    whatsapp_autoreply_template_id = fields.Many2one(
        "mail.whatsapp.template",
        string="Plantilla de respuesta automática",
        domain="[('state', '=', 'approved')]",
        help="Plantilla de WhatsApp que se envía al recibir un mensaje.",
    )
    whatsapp_autoreply_cooldown_hours = fields.Float(
        string="Horas entre respuestas automáticas",
        default=24.0,
        help="No se vuelve a responder en la misma conversación hasta que pasen "
        "estas horas desde la última respuesta automática. 0 = responder siempre.",
    )
