{
    "name": "Escudero - Respuesta automática WhatsApp",
    "version": "18.0.1.0.0",
    "category": "Services",
    "summary": "Responde automáticamente con una plantilla de WhatsApp a los mensajes entrantes.",
    "author": "Xtendoo",
    "website": "https://xtendoo.es",
    "license": "AGPL-3",
    "depends": [
        "escudero_resource_booking",
        "mail_gateway_whatsapp",
        "mail_gateway_whatsapp_variables",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
