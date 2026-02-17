# Copyright 2024 Xtendoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ResourceBooking(models.Model):
    _inherit = "resource.booking"

    has_overlap = fields.Boolean(
        compute="_compute_has_overlap",
        string="Has Overlap",
        help="Indicates if the booking overlaps with another one.",
    )

    @api.constrains("combination_id", "meeting_id", "type_id")
    def _check_scheduling(self):
        """Allow overlapping bookings by bypassing all validation."""
        # We bypass all checks to allow the user to save bookings even without 
        # resources or in case of overlap, as requested.
        return True

    def _get_best_combination(self):
        """Pick best combination based on current booking state, allowing busy ones."""
        res = super()._get_best_combination()
        if not res:
            # Fallback to the first combination defined for this type if none is free
            combinations = self.type_id.mapped("combination_rel_ids.combination_id")
            if combinations:
                return combinations[0]
        return res

    type_color = fields.Integer(
        string="Type Color",
        compute="_compute_type_color",
    )

    @api.depends("type_id.color")
    def _compute_type_color(self):
        for record in self:
            # We use the color directly from the type. 
            # If the picker is 1-indexed and calendar is 0-indexed, 
            # we'll handle any shift visually if needed, but starting simple.
            record.type_color = record.type_id.color or 0

    @api.depends("start", "duration", "combination_id")
    def _compute_has_overlap(self):
        """Compute if the booking overlaps with existing ones."""
        from odoo.addons.resource_booking.models.resource_booking import _availability_is_fitting
        for record in self:
            if not record.start or not record.stop or not record.combination_id:
                record.has_overlap = False
                continue
            
            start_dt = fields.Datetime.context_timestamp(record, record.start)
            end_dt = fields.Datetime.context_timestamp(record, record.stop)
            available_intervals = record._get_intervals(start_dt, end_dt)
            
            record.has_overlap = not _availability_is_fitting(available_intervals, start_dt, end_dt)
