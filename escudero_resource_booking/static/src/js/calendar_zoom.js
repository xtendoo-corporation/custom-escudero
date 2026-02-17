/** @odoo-module **/

import { CalendarController } from "@web/views/calendar/calendar_controller";
import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";
import { patch } from "@web/core/utils/patch";
import { useState, useEffect } from "@odoo/owl";
import { renderToString } from "@web/core/utils/render";

// 1. Controller Patch: Discrete Zoom & State Management
patch(CalendarController.prototype, {
    setup() {
        super.setup(...arguments);
        
        if (!this.state) {
            this.state = useState({});
        }
        
        const savedZoom = localStorage.getItem("calendar.zoom");
        // Steps of 0.5 are much more stable for CSS-based coordinate scaling
        this.state.zoomLevel = parseFloat(savedZoom || "1.0");
        if (isNaN(this.state.zoomLevel)) this.state.zoomLevel = 1.0;

        useEffect(
            () => {
                this.applyZoom();
            },
            () => [this.state.zoomLevel]
        );
    },

    zoomIn() {
        this.state.zoomLevel = Math.min(this.state.zoomLevel + 0.5, 3.0);
        localStorage.setItem("calendar.zoom", this.state.zoomLevel.toString());
    },

    zoomOut() {
        this.state.zoomLevel = Math.max(this.state.zoomLevel - 0.5, 1.0);
        localStorage.setItem("calendar.zoom", this.state.zoomLevel.toString());
    },

    applyZoom() {
        const level = this.state.zoomLevel;
        window.dispatchEvent(new CustomEvent('calendar:zoom_changed', { detail: level }));
        document.documentElement.style.setProperty('--calendar-zoom-level', level.toString());
    }
});

// 2. Renderer Patch: View Height Sync & Enhanced Context
patch(CalendarCommonRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        
        const syncZoom = (level) => {
            if (this.fc && this.fc.api) {
                // We no longer try to force-feed slotMinHeight to FC.
                // Our new strategy is Pure CSS Coordinate Scaling (SCSS transform).
                // We only call updateSize() to ensure scrollbars and view-total-height are correct.
                requestAnimationFrame(() => {
                    setTimeout(() => {
                        if (this.fc && this.fc.api) {
                            this.fc.api.updateSize();
                        }
                    }, 100);
                });
            }
        };

        useEffect(
            () => {
                const onZoomChanged = (ev) => syncZoom(ev.detail);
                window.addEventListener('calendar:zoom_changed', onZoomChanged);
                
                setTimeout(() => {
                    const currentLevel = parseFloat(localStorage.getItem("calendar.zoom") || "1.0");
                    syncZoom(currentLevel);
                }, 800);
                
                return () => {
                    window.removeEventListener('calendar:zoom_changed', onZoomChanged);
                };
            },
            () => []
        );
    },

    onEventContent(arg) {
        const event = arg.event;
        const record = this.props.model.records[event.id];
        
        if (record && this.props.model.resModel === 'resource.booking') {
            if (event.start && event.end) {
                const dateFmt = (date) => luxon.DateTime.fromJSDate(date).toFormat(this.timeFormat);
                arg.timeText = `${dateFmt(event.start)} - ${dateFmt(event.end)}`;
            }
            
            const context = {
                ...record,
                record: record,
                startTime: this.getStartTime(record),
                endTime: this.getEndTime(record),
                isResourceBooking: true,
            };
            
            const injectedContentStr = renderToString(this.constructor.eventTemplate, context);
            const domParser = new DOMParser();
            const { children } = domParser.parseFromString(injectedContentStr, "text/html").body;
            return { domNodes: children };
        }
        
        return super.onEventContent(arg);
    }
});
