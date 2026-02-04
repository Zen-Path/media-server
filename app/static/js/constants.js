// Mirror of EventType Enum
// prettier-ignore
export const EVENT_TYPE = Object.freeze({
    CREATE:     0,
    UPDATE:     1,
    DELETE:     2,
    PROGRESS:   3,
});

// Mirror of MediaType Enum
// prettier-ignore
export const MEDIA_TYPE = Object.freeze({
    GALLERY:    0,
    IMAGE:      1,
    VIDEO:      2,
    AUDIO:      3,
    TEXT:       4,
});

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

export const DOWNLOAD_STATUS = Object.freeze({
    PENDING: 0,
    IN_PROGRESS: 1,
    DONE: 2,
    FAILED: 3,
    MIXED: 4,
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
