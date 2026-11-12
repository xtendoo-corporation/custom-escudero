from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    whatsapp_autoreply_enabled = fields.Boolean(
        string="Respuesta automática de WhatsApp",
    )
    whatsapp_autoreply_mode = fields.Selection(
        [("template", "Plantilla"), ("text", "Texto personalizado")],
        string="Tipo de respuesta automática",
        default="template",
        required=True,
    )
    whatsapp_autoreply_text = fields.Text(
        string="Texto de respuesta automática",
        help="Texto que se envía como respuesta automática (texto libre).",
    )
    whatsapp_autoreply_template_id = fields.Many2one(
        "mail.whatsapp.template",
        string="Plantilla de respuesta automática",
        domain="[('state', '=', 'approved')]",
        help="Se envía su contenido, como texto libre, al recibir un mensaje "
        "(no como plantilla de Meta: se responde dentro de la ventana de 24 h).",
    )
    whatsapp_autoreply_cooldown_hours = fields.Float(
        string="Horas entre respuestas automáticas",
        default=24.0,
        help="No se vuelve a responder en la misma conversación hasta que pasen "
        "estas horas desde la última respuesta automática. 0 = responder siempre.",
    )
