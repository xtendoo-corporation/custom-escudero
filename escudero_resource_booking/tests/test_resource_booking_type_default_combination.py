# Copyright 2024 Xtendoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import common


class TestResourceBookingTypeDefaultCombination(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.resource_calendar = cls.env["resource.calendar"].create(
            {
                "name": "Default Combination Calendar",
            }
        )
        cls.resource_1 = cls.env["resource.resource"].create(
            {
                "name": "Default Combination Resource 1",
                "calendar_id": cls.resource_calendar.id,
            }
        )
        cls.resource_2 = cls.env["resource.resource"].create(
            {
                "name": "Default Combination Resource 2",
                "calendar_id": cls.resource_calendar.id,
            }
        )
        cls.first_combination = cls.env["resource.booking.combination"].create(
            {
                "resource_ids": [Command.set(cls.resource_1.ids)],
            }
        )
        cls.second_combination = cls.env["resource.booking.combination"].create(
            {
                "resource_ids": [Command.set(cls.resource_2.ids)],
            }
        )

    def test_default_get_prefills_first_combination(self):
        defaults = self.env["resource.booking.type"].default_get(["combination_rel_ids"])

        self.assertTrue(defaults["combination_rel_ids"])
        self.assertEqual(
            defaults["combination_rel_ids"][0][2]["combination_id"],
            self.first_combination.id,
        )

    def test_create_prefills_first_combination_when_missing(self):
        booking_type = self.env["resource.booking.type"].create(
            {
                "name": "Booking Type Without Combination",
                "resource_calendar_id": self.resource_calendar.id,
            }
        )

        self.assertEqual(len(booking_type.combination_rel_ids), 1)
        self.assertEqual(
            booking_type.combination_rel_ids.combination_id,
            self.first_combination,
        )

    def test_create_keeps_explicit_combination(self):
        booking_type = self.env["resource.booking.type"].create(
            {
                "name": "Booking Type With Explicit Combination",
                "resource_calendar_id": self.resource_calendar.id,
                "combination_rel_ids": [
                    Command.create(
                        {
                            "combination_id": self.second_combination.id,
                            "sequence": 5,
                        }
                    )
                ],
            }
        )

        self.assertEqual(len(booking_type.combination_rel_ids), 1)
        self.assertEqual(
            booking_type.combination_rel_ids.combination_id,
            self.second_combination,
        )

