# Copyright 2024 Xtendoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models


class ResourceBookingType(models.Model):
    _inherit = "resource.booking.type"

    color = fields.Integer(string="Color")

    def _get_default_combination_rel_command(self):
        first_combination = self.env["resource.booking.combination"].search([], limit=1)
        if not first_combination:
            return False
        return Command.create(
            {
                "combination_id": first_combination.id,
            }
        )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if "combination_rel_ids" in fields_list and not defaults.get("combination_rel_ids"):
            command = self._get_default_combination_rel_command()
            if command:
                defaults["combination_rel_ids"] = [command]
        return defaults

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered(lambda booking_type: not booking_type.combination_rel_ids):
            command = record._get_default_combination_rel_command()
            if command:
                record.write({"combination_rel_ids": [command]})
        return records

