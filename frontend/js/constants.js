import { MEDIA_TYPE, DOWNLOAD_STATUS } from "../../shared/constants.js";

export * from "../../shared/constants.js";

export const VALID_MEDIA_TYPES = Object.values(MEDIA_TYPE);

export const MEDIA_TYPE_CONFIG = Object.freeze({
    [MEDIA_TYPE.GALLERY]: {
        icon: "fa-layer-group",
        className: "type-gallery",
        label: "Gallery",
    },
    [MEDIA_TYPE.IMAGE]: {
        icon: "fa-image",
        className: "type-image",
        label: "Image",
    },
    [MEDIA_TYPE.VIDEO]: {
        icon: "fa-film",
        className: "type-video",
        label: "Video",
    },
    [MEDIA_TYPE.AUDIO]: {
        icon: "fa-microphone",
        className: "type-audio",
        label: "Audio",
    },
    [MEDIA_TYPE.TEXT]: {
        icon: "fa-file-lines",
        className: "type-text",
        label: "Text",
    },
    UNKNOWN: {
        icon: "fa-circle-question",
        className: "type-unknown",
        label: "Unknown",
    },
});

export const STATUS_CONFIG = Object.freeze({
    [DOWNLOAD_STATUS.PENDING]: {
        label: "Pending",
        icon: "fa-clock",
        color: "text-muted",
    },
    [DOWNLOAD_STATUS.IN_PROGRESS]: {
        label: "In Progress",
        icon: "fa-spinner fa-spin",
        color: "text-primary",
    },
    [DOWNLOAD_STATUS.DONE]: {
        label: "Completed",
        icon: "fa-check-circle",
        color: "text-success",
    },
    [DOWNLOAD_STATUS.FAILED]: {
        label: "Failed",
        icon: "fa-times-circle",
        color: "text-danger",
    },
    [DOWNLOAD_STATUS.MIXED]: {
        label: "Mixed",
        icon: "fa-circle-exclamation",
        color: "text-warning",
    },
    UNKNOWN: { label: "Unknown", icon: "fa-question", color: "text-muted" },
});

export class ColumnData {
    constructor({
        id,
        label = null,
        field = null,
        sortable = false,
        cssClass = null,
        icon = null,
    }) {
        this.id = id;
        this.label = label;
        this.field = field;
        this.sortable = sortable;
        this.cssClass = cssClass;
        this.icon = icon;
    }
}
