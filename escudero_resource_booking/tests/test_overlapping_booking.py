# Copyright 2024 Xtendoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo.fields import Datetime
from datetime import timedelta

class TestOverlappingBooking(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.resource_calendar = cls.env["resource.calendar"].create({
            "name": "Test Calendar",
        })
        cls.resource = cls.env["resource.resource"].create({
            "name": "Test Resource",
            "calendar_id": cls.resource_calendar.id,
        })
        cls.booking_type = cls.env["resource.booking.type"].create({
            "name": "Test Booking Type",
            "resource_calendar_id": cls.resource_calendar.id,
        })
        cls.combination = cls.env["resource.booking.combination"].create({
            "resource_ids": [(4, cls.resource.id)],
        })
        cls.env["resource.booking.type.combination.rel"].create({
            "type_id": cls.booking_type.id,
            "combination_id": cls.combination.id,
        })
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

    def test_overlapping_booking_creation(self):
        """Verify that we can create two bookings at the same time for the same resource."""
        start = Datetime.now() + timedelta(days=1, hours=10) # Future date
        duration = 1.0
        
        # Create first booking
        booking1 = self.env["resource.booking"].create({
            "name": "Booking 1",
            "partner_ids": [(4, self.partner.id)],
            "type_id": self.booking_type.id,
            "combination_id": self.combination.id,
        })
        
        # Schedule it
        meeting1 = self.env["calendar.event"].create({
            "name": "Meeting 1",
            "start": start,
            "stop": start + timedelta(hours=duration),
            "duration": duration,
            "resource_booking_ids": [(4, booking1.id)],
        })
        
        # Verify first booking is scheduled
        self.assertEqual(booking1.state, "scheduled")
        
        # Create second booking at the same time
        booking2 = self.env["resource.booking"].create({
            "name": "Booking 2",
            "partner_ids": [(4, self.partner.id)],
            "type_id": self.booking_type.id,
            "combination_id": self.combination.id,
        })
        
        # In the original module, scheduling this would raise a ValidationError
        # because the resource is already busy with booking1.
        meeting2 = self.env["calendar.event"].create({
            "name": "Meeting 2",
            "start": start,
            "stop": start + timedelta(hours=duration),
            "duration": duration,
            "resource_booking_ids": [(4, booking2.id)],
        })
        
        # Verify second booking is also scheduled (overlapping allowed)
        self.assertEqual(booking2.state, "scheduled")
        self.assertEqual(booking2.meeting_id.id, meeting2.id)

    def test_onchange_warning(self):
        """Verify that the onchange returns a warning when overlapping."""
        start = Datetime.now() + timedelta(days=1, hours=10)
        duration = 1.0
        
        # Create first booking and meeting
        booking1 = self.env["resource.booking"].create({
            "name": "Booking 1",
            "partner_ids": [(4, self.partner.id)],
            "type_id": self.booking_type.id,
            "combination_id": self.combination.id,
        })
        self.env["calendar.event"].create({
            "name": "Meeting 1",
            "start": start,
            "stop": start + timedelta(hours=duration),
            "duration": duration,
            "resource_booking_ids": [(4, booking1.id)],
        })
        
        # Simulate onchange for a new booking
        new_booking = self.env["resource.booking"].new({
            "type_id": self.booking_type.id,
            "combination_id": self.combination.id,
            "start": start,
            "duration": duration,
        })
        
        # The stop is usually computed
        new_booking._compute_stop()
        
        warning = new_booking._onchange_check_overlap()
        self.assertIsNotNone(warning)
        self.assertIn("warning", warning)
        self.assertEqual(warning["warning"]["title"], "Overlap Detected")
