/** @odoo-module **/

import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";
import { patch } from "@web/core/utils/patch";
import { renderToString } from "@web/core/utils/render";

// Renderer Patch: Custom event content for resource.booking
patch(CalendarCommonRenderer.prototype, {
    get options() {
        const options = super.options;
        if (this.props.model.resModel === 'resource.booking') {
            // Events side by side instead of overlapping
            options.slotEventOverlap = false;
        }
        return options;
    },

    onEventContent(arg) {
        const event = arg.event;
        const record = this.props.model.records[event.id];

        if (record && this.props.model.resModel === 'resource.booking') {
            const dateFmt = (date) => luxon.DateTime.fromJSDate(date).toFormat(this.timeFormat);
            if (event.start && event.end) {
                arg.timeText = `${dateFmt(event.start)} - ${dateFmt(event.end)}`;
            }

            // Resolve partner names from model filters
            let partnerNames = "";
            const rawRecord = record.rawRecord;
            if (rawRecord && rawRecord.partner_ids) {
                const partnerIds = Array.isArray(rawRecord.partner_ids) ? rawRecord.partner_ids : [];
                const partnerSection = this.props.model.data.filterSections.partner_ids;
                if (partnerSection && partnerSection.filters) {
                    const names = partnerIds.map(id => {
                        const filter = partnerSection.filters.find(f => f.value === id);
                        return filter ? filter.label : null;
                    }).filter(n => n);
                    partnerNames = names.join(", ");
                }
            }

            const context = {
                ...record,
                record: record,
                startTime: this.getStartTime(record),
                endTime: this.getEndTime(record),
                timeText: arg.timeText,
                startTimeText: event.start ? dateFmt(event.start) : "",
                isResourceBooking: true,
                partnerNames: partnerNames,
            };

            const injectedContentStr = renderToString(this.constructor.eventTemplate, context);
            const domParser = new DOMParser();
            const { children } = domParser.parseFromString(injectedContentStr, "text/html").body;
            return { domNodes: children };
        }

        return super.onEventContent(arg);
    }
});

