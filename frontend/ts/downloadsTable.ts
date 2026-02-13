import { BaseDataRow, BaseDataTable } from "./baseDataTable";
import {
    VALID_MEDIA_TYPES,
    MEDIA_TYPE_CONFIG,
    ColumnData,
    STATUS_CONFIG,
    DOWNLOAD_STATUS,
} from "./constants";
import { toLocalStandardTime, formatDuration } from "./utils";
import { createMenuTrigger } from "./dropdownHelper";
import { ModalManager } from "./modalManager";
import { copyToClipboard, createIconLabelPair } from "./utils";
import { showToast } from "./utils";
import { handleBulkDelete } from "./controllers";

export class DownloadsTable extends BaseDataTable {
    constructor(container: HTMLElement) {
        super(container);

        this.columnsMap = {
            CHECKBOX: new ColumnData({
                id: "checkbox",
                field: "isSelected",
                sortable: true,
                cssClass: "col-checkbox",
            }),
            ID: new ColumnData({
                id: "id",
                label: "ID",
                field: "id",
                sortable: true,
                cssClass: "col-id",
                icon: "fa-hashtag",
            }),
            MEDIA_TYPE: new ColumnData({
                id: "media-type",
                label: "Media Type",
                field: "mediaType",
                sortable: true,
                cssClass: "col-media-type",
                icon: "fa-image",
            }),
            NAME: new ColumnData({
                id: "name",
                label: "Name",
                field: "title",
                sortable: true,
                cssClass: "col-name",
                icon: "fa-quote-left",
            }),
            START_TIME: new ColumnData({
                id: "start-time",
                label: "Start Time",
                field: "startTime",
                sortable: true,
                cssClass: "col-start-time",
                icon: "fa-clock",
            }),
            STATUS: new ColumnData({
                id: "status",
                label: "Status",
                field: "status",
                sortable: true,
                cssClass: "col-status",
                icon: "fa-circle-check",
            }),
            ACTIONS: new ColumnData({
                id: "actions",
                cssClass: "col-actions",
            }),
        };
        this.columnsList = Object.values(this.columnsMap);

        this.init();
    }

    add(entries: any) {
        this._addEntries(entries, DownloadRow, this);
    }

    _createActions() {
        const actions = [
            {
                label: "Edit Selected",
                icon: "fa-pen",
                onClick: () => {
                    ModalManager.openEdit(this.getProcessableEntries());
                },
            },
            {
                label: "Copy Selected URLs",
                icon: "fa-link",
                onClick: async () => {
                    const result = await this.copyFields("url", true);
                    if (result) {
                        showToast("URLs copied to clipboard!", "success");
                    } else {
                        showToast("Could not copy URLs.", "error");
                    }
                    return result;
                },
            },
            {
                label: "Copy Selected Titles",
                icon: "fa-quote-left",
                onClick: async () => {
                    const result = await this.copyFields("title", true);
                    if (result) {
                        showToast("Titles copied to clipboard!");
                    } else {
                        showToast("Could not copy titles.", "error");
                    }
                    return result;
                },
            },
            {
                label: "Delete Selected",
                icon: "fa-trash",
                className: "text-danger",
                onClick: () => {
                    const ids = this.getProcessableEntries().map(
                        (item) => item.data.id
                    );
                    handleBulkDelete(ids);
                },
            },
        ];

        return createMenuTrigger(actions);
    }

    getStatsString() {
        const total = this.entryList.length;
        if (total === 0) return "Table is empty.";

        const selected = this.selectedCount;
        const visible = this.entryList.filter((e) => e._isVisible).length;

        // Build frequency maps dynamically
        const stats = this.entryList.reduce(
            (acc, entry) => {
                const { mediaType, status } = entry.data;
                acc.mediaTypes[mediaType] =
                    (acc.mediaTypes[mediaType] || 0) + 1;
                acc.statuses[status] = (acc.statuses[status] || 0) + 1;
                return acc;
            },
            { mediaTypes: {}, statuses: {} }
        );

        const formatGroup = (title, dataMap, config) => {
            let str = `\n[ ${title} ]\n`;
            Object.entries(dataMap).forEach(([key, count]) => {
                const label = config[key]?.label || `Unknown (${key})`;
                str += `  - ${label.padEnd(15)}: ${count}\n`;
            });
            return str;
        };

        let report = `=== Table Summary (${new Date().toLocaleTimeString()}) ===\n`;
        report += `Total Rows:      ${total}\n`;
        report += `Selected:        ${selected} (${((selected / total) * 100).toFixed(1)}%)\n`;
        report += `Visible:         ${visible} / ${total}\n`;

        // Distribution sections
        report += formatGroup(
            "Media Types",
            stats.mediaTypes,
            MEDIA_TYPE_CONFIG
        );
        report += formatGroup("Statuses", stats.statuses, STATUS_CONFIG);

        return report;
    }
}

export class DownloadRow extends BaseDataRow {
    constructor(data: any, tableRef: any) {
        super(data, tableRef);
        // Initializing data here due to private methods
        this.initData(data);
    }

    initData(data) {
        this.data.id = this.#validateNumberField(data.id);

        this.data.title = this.#validateTextField(data.title);
        this.data.url = this.#validateTextField(data.url);

        this.data.mediaType = this.#validateIntOptionsField(
            data.mediaType,
            VALID_MEDIA_TYPES
        );

        this.data.startTime = this.#validateDateField(data.startTime);
        this.data.endTime = this.#validateDateField(data.endTime);
        this.data.updateTime = this.#validateDateField(data.updateTime);

        this.data.status = this.#validateIntOptionsField(
            data.status,
            Object.values(DOWNLOAD_STATUS)
        );
        this.data.statusMessage = this.#validateTextField(data.statusMessage);

        this.displayValues = {
            id: this.data.id >= 0 ? `#${this.data.id}` : "N/A",
            title: this.data.title !== "" ? this.data.title : "Untitled",
            url: this.data.url !== "" ? this.data.url : "Unknown",

            startTime: this.#formatDateField(this.data.startTime),
            endTime: this.#formatDateField(this.data.endTime),
            updateTime: this.#formatDateField(this.data.updateTime),
        };

        this.sortValues = {
            id: this.data.id,
            title: this.data.title.toLowerCase(),
            url: this.data.url,
            mediaType: this.data.mediaType,

            startTime: this.data.startTime,
            endTime: this.data.endTime,
            updateTime: this.data.updateTime,
            status: this.data.status,
            isSelected: this.isSelected,
        };

        // TODO: temporary workaround until we implement proper filter UI
        this.searchIndex =
            `${this.displayValues.title} ${this.displayValues.url} ${this.displayValues.id}`.toLowerCase();
    }

    #validateNumberField(value: number) {
        if (typeof value === "number" && value >= 0) {
            return value;
        }
        return -1;
    }

    #validateTextField(value: string) {
        if (typeof value === "string" && value.trim().length > 0) {
            return value.trim();
        }
        return "";
    }

    #validateDateField(value: number) {
        if (typeof value !== "number") {
            return 0;
        }

        // We multiply by 1000 because JS uses milliseconds
        const date = new Date(value * 1000);
        if (value < 0 || isNaN(date.getTime())) {
            return 0;
        }

        return value;
    }

    #validateIntOptionsField(value: number, options: number[]) {
        if (typeof value !== "number") return -1;
        if (options.includes(value)) return value;
    }

    #formatDateField(value: number) {
        if (value === 0) return "-";
        return toLocalStandardTime(value);
    }

    render() {
        this.dom.row = document.createElement("div");
        this.dom.row.classList.add("data-row");

        const columns = this.table.columnsMap;
        this.table.columnsList.forEach((col) => {
            const cell = document.createElement("div");
            cell.className = `cell ${col.cssClass || ""}`;

            switch (col.id) {
                case columns.CHECKBOX.id:
                    this.dom.checkbox = this.#renderCheckbox();
                    cell.append(this.dom.checkbox);
                    break;
                case columns.MEDIA_TYPE.id:
                    cell.append(this.#renderMediaContent());
                    this.dom.mediaTypeCell = cell;
                    break;
                case columns.NAME.id:
                    cell.append(this.#renderNameContent());
                    break;
                case columns.START_TIME.id:
                    cell.textContent = this.displayValues.startTime;
                    cell.title = this.#generateTimeDiffTooltip();
                    this.dom.startTimeEl = cell;
                    break;
                case columns.STATUS.id:
                    cell.append(this.#renderStatusContent());
                    this.dom.statusCell = cell;
                    break;
                case columns.ACTIONS.id:
                    cell.append(this.#renderActions());
                    break;
                default:
                    cell.textContent = this.displayValues[col.field] ?? "";
            }

            this.dom.row.appendChild(cell);
        });

        return this.dom.row;
    }

    #renderCheckbox() {
        const input = document.createElement("input");
        input.type = "checkbox";
        input.checked = this.isSelected;
        input.onclick = (e) => {
            this.isSelected = e.target.checked;
        };

        // Allow user to shift-click select multiple rows at a time
        input.onclick = (e) => {
            e.stopPropagation(); // Prevent sort trigger

            const currentIndex = this.table.entryList.indexOf(this);

            if (e.shiftKey && this.table.lastSelectedIndex !== null) {
                const start = Math.min(
                    this.table.lastSelectedIndex,
                    currentIndex
                );
                const end = Math.max(
                    this.table.lastSelectedIndex,
                    currentIndex
                );

                // Select everything in the range
                for (let i = start; i <= end; i++) {
                    this.table.entryList[i].isSelected = e.target.checked;
                }
            } else {
                this.isSelected = e.target.checked;
                this.table.lastSelectedIndex = currentIndex;
            }
        };

        return input;
    }

    #renderMediaContent() {
        const config =
            MEDIA_TYPE_CONFIG[this.data.mediaType] ?? MEDIA_TYPE_CONFIG.UNKNOWN;

        return createIconLabelPair({
            icon: config.icon,
            label: config.label,
            extraClasses: [config.className],
            title: config.label,
        });
    }

    #renderNameContent() {
        const container = document.createElement("a");
        container.href = this.data.url;
        container.target = "_blank";

        const titleEl = document.createElement("span");
        titleEl.classList.add("title", "truncate");
        titleEl.title = this.displayValues.title;
        titleEl.textContent = this.displayValues.title;

        const urlEl = document.createElement("span");
        urlEl.classList.add("url", "truncate");
        urlEl.title = this.displayValues.url;
        urlEl.textContent = this.displayValues.url;

        this.dom.titleEl = titleEl;
        this.dom.urlEl = urlEl;

        container.append(titleEl, urlEl);
        return container;
    }

    #generateTimeDiffTooltip() {
        const startMs = this.sortValues.startTime * 1000;

        const endMs =
            this.data.endTime !== 0 ? this.data.endTime * 1000 : Date.now(); // Date.now() is already in ms

        const diff = endMs - startMs;
        const diffHumanReadable = formatDuration(diff);

        if (this.data.endTime === 0) {
            return `Running for ${diffHumanReadable}`;
        }

        return `Finished at ${toLocalStandardTime(this.data.endTime)} (took ${diffHumanReadable})`;
    }

    #renderStatusContent() {
        const config = STATUS_CONFIG[this.data.status] ?? STATUS_CONFIG.UNKNOWN;

        return createIconLabelPair({
            icon: config.icon,
            label: config.label,
            extraClasses: [config.color],
            title: config.label,
        });
    }

    #renderActions() {
        const actions = [
            {
                label: "Edit Entry",
                icon: "fa-pen",
                onClick: () => {
                    ModalManager.openEdit(this);
                },
            },
            {
                label: "Copy Title",
                icon: "fa-quote-left",
                onClick: async () => {
                    const result = await copyToClipboard(this.data.title);
                    if (result) {
                        showToast("Title copied to clipboard!", "success");
                    } else {
                        showToast("Could not copy the title.", "error");
                    }
                },
            },
            {
                label: "Copy URL",
                icon: "fa-link",
                onClick: async () => {
                    const result = await copyToClipboard(this.data.url);
                    if (result) {
                        showToast("URL copied to clipboard!", "success");
                    } else {
                        showToast("Could not copy the URL.", "error");
                    }
                },
            },
            {
                label: "Delete Entry",
                icon: "fa-trash",
                className: "text-danger",
                onClick: () => {
                    handleBulkDelete([this.data.id]);
                },
            },
        ];

        return createMenuTrigger(actions);
    }

    update(newData) {
        const supportedFields = ["title", "mediaType", "status"];
        const changedFields = Object.keys(newData).filter(
            (key) =>
                supportedFields.includes(key) &&
                newData[key] !== undefined &&
                newData[key] !== this.data[key]
        );

        if (changedFields.length === 0) return;

        changedFields.forEach((field) => {
            switch (field) {
                case "title":
                    this.data.title = newData.title;
                    this.initData(this.data);
                    if (this.dom.titleEl) {
                        this.dom.titleEl.textContent = this.displayValues.title;
                    }
                    break;

                case "mediaType":
                    this.data.mediaType = newData.mediaType;
                    if (this.dom.mediaTypeCell) {
                        this.dom.mediaTypeCell.replaceChildren(
                            this.#renderMediaContent()
                        );
                    }
                    break;

                case "status":
                    this.data.status = newData.status;
                    if (this.dom.statusCell) {
                        this.dom.statusCell.replaceChildren(
                            this.#renderStatusContent()
                        );
                    }
                    if (this.dom.startTimeEl) {
                        this.dom.startTimeEl.title =
                            this.#generateTimeDiffTooltip();
                    }
                    break;
            }
        });

        // Prevent stacking
        this.dom.row.classList.remove("row-pulse");

        // This is necessary to restart the animation if it was already playing
        void this.dom.row.offsetWidth;

        this.dom.row.classList.add("row-pulse");
        this.dom.row.addEventListener(
            "animationend",
            () => {
                this.dom.row.classList.remove("row-pulse");
            },
            { once: true }
        );

        this.initData(this.data);
    }
}
