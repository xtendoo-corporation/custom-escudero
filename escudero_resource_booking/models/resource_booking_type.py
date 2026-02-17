# Copyright 2024 Xtendoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

class ResourceBookingType(models.Model):
    _inherit = "resource.booking.type"

    color = fields.Integer(string="Color")
