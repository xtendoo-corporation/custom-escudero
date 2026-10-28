import logging
from datetime import timedelta

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MailGatewayWhatsapp(models.AbstractModel):
    _inherit = "mail.gateway.whatsapp"

    def _process_update(self, chat, message, value):
        last_message_id = chat.sudo().message_ids[:1].id
        super()._process_update(chat, message, value)
        received = chat.sudo().message_ids.filtered(
            lambda m: m.id > last_message_id and m.message_type == "comment"
        )
        if not received:
            # Nothing was posted (reaction, unsupported type...): nobody to answer.
            return
        try:
            with self.env.cr.savepoint():
                self._whatsapp_autoreply(chat, value)
        except Exception:  # noqa: BLE001
            # The incoming message must be kept whatever happens to the reply.
            _logger.exception("WhatsApp autoreply failed for channel %s", chat.id)

    def _whatsapp_autoreply_template(self, chat):
        company = chat.gateway_id.company_id or self.env.company
        if not company.whatsapp_autoreply_enabled:
            return self.env["mail.whatsapp.template"]
        template = company.whatsapp_autoreply_template_id
        if template.state != "approved" or template.gateway_id != chat.gateway_id:
            return self.env["mail.whatsapp.template"]
        return template

    def _whatsapp_autoreply_in_cooldown(self, chat, company):
        hours = company.whatsapp_autoreply_cooldown_hours
        last = chat.sudo().last_autoreply_date
        return bool(hours and last and fields.Datetime.now() < last + timedelta(hours=hours))

    def _whatsapp_autoreply(self, chat, value):
        chat = chat.sudo()
        template = self._whatsapp_autoreply_template(chat)
        if not template:
            return False
        company = chat.gateway_id.company_id or self.env.company
        if self._whatsapp_autoreply_in_cooldown(chat, company):
            return False
        author = self._get_author(chat.gateway_id, value)
        partner = author if author and author._name == "res.partner" else False
        if partner and len(partner) > 1:
            partner = partner[0]
        if not partner:
            if template.variable_ids:
                _logger.info(
                    "WhatsApp autoreply skipped on channel %s: unknown contact "
                    "and template has variables",
                    chat.id,
                )
                return False
            # No variables to fill in, any record will do to render the template.
            partner = company.partner_id
        template = template.with_context(default_res_id=partner.id)
        chat.last_autoreply_date = fields.Datetime.now()
        chat.with_context(
            whatsapp_template_id=template.id, default_res_id=partner.id
        ).message_post(
            body=template.render_body_message(),
            # Explicit author so mail_gateway_whatsapp_variables does not take
            # our own reply for an incoming message.
            author_id=self.env.user.partner_id.id,
            subtype_xmlid="mail.mt_comment",
            message_type="comment",
        )
        return True
