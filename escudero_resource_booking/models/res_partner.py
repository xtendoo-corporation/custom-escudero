from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_view_resource_booking(self):
        # We inherit the logic but override the action to force list view by default
        action = super().action_view_resource_booking()
        
        # Odoo 18 uses list, not tree for view_mode in many cases, but list is safer
        action["view_mode"] = "list,calendar,form"
        
        # We ensure the views are prioritized correctly
        action["views"] = [
            (self.env.ref("resource_booking.resource_booking_view_tree").id, "list"),
            (self.env.ref("resource_booking.resource_booking_view_calendar").id, "calendar"),
            (self.env.ref("resource_booking.resource_booking_view_form").id, "form"),
        ]
        return action
