{
    "name": "Escudero - Citas",
    "version": "1.0.1",
    "category": "Services",
    "summary": "Permite solapamiento de citas con avisos.",
    "author": "Xtendoo",
    "website": "https://xtendoo.es",
    "depends": ["resource_booking"],
    "data": [
        "views/resource_booking_views.xml",
        "views/res_partner_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "escudero_resource_booking/static/src/scss/calendar_zoom.scss",
            "escudero_resource_booking/static/src/js/calendar_event_renderer.js",
            "escudero_resource_booking/static/src/xml/calendar_zoom.xml",
        ],
    },
    "installable": True,
    "application": False,
    "license": "AGPL-3",
}
