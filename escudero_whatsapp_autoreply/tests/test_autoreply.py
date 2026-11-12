from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWhatsappAutoreply(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        cls.gateway = cls.env["mail.gateway"].create(
            {
                "name": "Autoreply gateway",
                "gateway_type": "whatsapp",
                "token": "token",
                "whatsapp_security_key": "key",
                "webhook_secret": "SECRET",
                "company_id": cls.company.id,
            }
        )
        cls.template = cls._create_template("Autoreply", "Hola {{1}}, gracias.")
        cls.partner = cls.env["res.partner"].create(
            {"name": "Cliente Test", "mobile": "+34 611 222 333"}
        )
        cls.company.write(
            {
                "whatsapp_autoreply_enabled": True,
                "whatsapp_autoreply_template_id": cls.template.id,
                "whatsapp_autoreply_cooldown_hours": 24.0,
            }
        )
        # The {{1}} variable is generated from the body.
        cls.template.variable_ids.write({"field_name": "name"})

    @classmethod
    def _create_template(cls, name, body, **kwargs):
        vals = {
            "name": name,
            "body": body,
            "category": "utility",
            "language": "es",
            "state": "approved",
            "is_supported": True,
            "gateway_id": cls.gateway.id,
            "model_id": cls.env["ir.model"]._get_id("res.partner"),
        }
        vals.update(kwargs)
        return cls.env["mail.whatsapp.template"].create(vals)

    def _payload(self, wa_id="34611222333", body="Hola", extra=None):
        message = {
            "from": wa_id,
            "id": "wamid.IN",
            "timestamp": "1234",
            "type": "text",
            "text": {"body": body},
        }
        message.update(extra or {})
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WABA",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "contacts": [
                                    {"profile": {"name": "NAME"}, "wa_id": wa_id}
                                ],
                                "messages": [message],
                            },
                        }
                    ],
                }
            ],
        }

    def _receive(self, payload=None):
        """Receive a message, returning the mocked ``requests.post``."""
        with patch("requests.post") as post_mock:
            response = MagicMock(status_code=200)
            response.json.return_value = {"messages": [{"id": "wamid.OUT"}]}
            post_mock.return_value = response
            # Same as the webhook controller (gateway.py): dispatcher and gateway
            # both live in an env with no_gateway_notification=True.
            dispatcher = self.env["mail.gateway.whatsapp"].with_context(
                no_gateway_notification=True
            )
            dispatcher._receive_update(
                dispatcher.env["mail.gateway"].browse(self.gateway.id),
                payload or self._payload(),
            )
        return post_mock

    def _channel(self, wa_id="34611222333"):
        return self.env["discuss.channel"].browse(self.gateway._get_channel_id(wa_id))

    def _reply_calls(self, post_mock):
        return [
            call
            for call in post_mock.call_args_list
            if call.kwargs.get("json", {}).get("type") == "text"
        ]

    def test_reply_sent_as_free_text(self):
        post_mock = self._receive()
        calls = self._reply_calls(post_mock)
        self.assertEqual(len(calls), 1)
        payload = calls[0].kwargs["json"]
        self.assertEqual(payload["to"], "34611222333")
        # Free text built from the template, not a template message.
        self.assertNotIn("template", payload)
        self.assertEqual(payload["text"]["body"], "Hola Cliente Test, gracias.")
        self.assertFalse(
            [
                c
                for c in post_mock.call_args_list
                if c.kwargs.get("json", {}).get("type") == "template"
            ]
        )
        channel = self._channel()
        self.assertTrue(channel.last_autoreply_date)
        outgoing = channel.message_ids.filtered(
            lambda m: m.message_type == "comment" and "Hola" in m.body
            and m.author_id != self.partner
        )
        self.assertEqual(len(outgoing), 1)
        self.assertIn("Cliente Test", outgoing.body)
        # The reply must have gone through the gateway (a single time).
        notification = outgoing.notification_ids.filtered(
            lambda n: n.notification_type == "gateway"
        )
        self.assertEqual(len(notification), 1)
        self.assertEqual(notification.notification_status, "sent")
        self.assertEqual(notification.gateway_message_id, "wamid.OUT")

    def test_multiline_body_keeps_line_breaks(self):
        template = self._create_template("Multi", "Primera línea\nSegunda línea")
        self.company.whatsapp_autoreply_template_id = template
        calls = self._reply_calls(self._receive())
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0].kwargs["json"]["text"]["body"], "Primera línea\nSegunda línea"
        )

    def test_custom_text_reply(self):
        self.company.write(
            {
                "whatsapp_autoreply_mode": "text",
                "whatsapp_autoreply_text": "Te respondemos en breve.",
                "whatsapp_autoreply_template_id": False,
            }
        )
        # Works even for unknown contacts.
        calls = self._reply_calls(self._receive(self._payload(wa_id="34699000111")))
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0].kwargs["json"]["text"]["body"], "Te respondemos en breve."
        )

    def test_custom_text_empty_does_not_reply(self):
        self.company.write(
            {"whatsapp_autoreply_mode": "text", "whatsapp_autoreply_text": "  "}
        )
        self.assertFalse(self._reply_calls(self._receive()))

    def test_disabled_does_not_reply(self):
        self.company.whatsapp_autoreply_enabled = False
        post_mock = self._receive()
        self.assertFalse(self._reply_calls(post_mock))
        self.assertFalse(self._channel().last_autoreply_date)
        self.assertEqual(len(self._channel().message_ids), 1)

    def test_no_template_does_not_reply(self):
        self.company.whatsapp_autoreply_template_id = False
        self.assertFalse(self._reply_calls(self._receive()))

    def test_not_approved_template_does_not_reply(self):
        self.template.state = "draft"
        self.assertFalse(self._reply_calls(self._receive()))

    def test_template_of_other_gateway_does_not_reply(self):
        other = self.env["mail.gateway"].create(
            {
                "name": "Other gateway",
                "gateway_type": "whatsapp",
                "token": "other_token",
                "whatsapp_security_key": "other_key",
                "webhook_secret": "OTHER",
            }
        )
        self.template.gateway_id = other
        self.assertFalse(self._reply_calls(self._receive()))

    def test_cooldown(self):
        self.assertEqual(len(self._reply_calls(self._receive())), 1)
        # Second message right away: no new reply.
        self.assertFalse(self._reply_calls(self._receive()))
        # After the cooldown: replies again.
        self._channel().last_autoreply_date = fields.Datetime.now() - timedelta(
            hours=25
        )
        self.assertEqual(len(self._reply_calls(self._receive())), 1)

    def test_cooldown_zero_always_replies(self):
        self.company.whatsapp_autoreply_cooldown_hours = 0
        self.assertEqual(len(self._reply_calls(self._receive())), 1)
        self.assertEqual(len(self._reply_calls(self._receive())), 1)

    def test_unknown_contact_with_variables_skipped(self):
        post_mock = self._receive(self._payload(wa_id="34699000111"))
        self.assertFalse(self._reply_calls(post_mock))
        # The incoming message is kept.
        self.assertEqual(len(self._channel("34699000111").message_ids), 1)

    def test_unknown_contact_without_variables_replies(self):
        template = self._create_template("Plain", "Gracias por escribirnos")
        self.company.whatsapp_autoreply_template_id = template
        post_mock = self._receive(self._payload(wa_id="34699000111"))
        self.assertEqual(len(self._reply_calls(post_mock)), 1)

    def test_message_without_content_is_ignored(self):
        payload = self._payload(extra={"type": "reaction"})
        payload["entry"][0]["changes"][0]["value"]["messages"][0].pop("text")
        self.assertFalse(self._reply_calls(self._receive(payload)))

    def test_failure_in_reply_keeps_incoming_message(self):
        with patch.object(
            type(self.env["mail.gateway.whatsapp"]),
            "_whatsapp_autoreply",
            side_effect=ValueError("boom"),
        ):
            self._receive()
        channel = self._channel()
        self.assertEqual(len(channel.message_ids), 1)
        self.assertEqual(channel.message_ids.author_id, self.partner)

    def test_settings(self):
        settings = self.env["res.config.settings"].create(
            {
                "whatsapp_autoreply_enabled": True,
                "whatsapp_autoreply_template_id": self.template.id,
                "whatsapp_autoreply_cooldown_hours": 6.0,
            }
        )
        settings.execute()
        self.assertTrue(self.company.whatsapp_autoreply_enabled)
        self.assertEqual(self.company.whatsapp_autoreply_template_id, self.template)
        self.assertEqual(self.company.whatsapp_autoreply_cooldown_hours, 6.0)
