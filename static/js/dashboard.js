import { EVENT_TYPE } from "./constants.js";
import { handleColorScheme, debounce, StreamManager } from "./utils.js";
import { DownloadsTable } from "./downloadsTable.js";

const debouncedFilter = debounce((searchValue) => {
    requestAnimationFrame(() => {
        downloadsTable.filter(searchValue);
    });
}, 10);

// Only starts filtering after a small delay
function filterTable() {
    const searchValue = document.getElementById("searchInput").value;

    const clearBtn = document.getElementById("clearBtn");
    if (clearBtn) {
        clearBtn.classList.toggle("show", searchValue.length > 0);
    }

    debouncedFilter(searchValue);
}

// Updates UI and filters the table instantly
function clearSearch() {
    const input = document.getElementById("searchInput");
    input.value = "";

    document.getElementById("clearBtn").classList.remove("show");
    downloadsTable.filter("");

    input.focus();
}

function bulkDelete(ids) {
    if (ids.length === 0) {
        alert("No items selected or visible to delete.");
        return false;
    }

    if (!confirm(`Delete ${ids.length} entries?`)) {
        return false;
    }

    fetch("/api/bulkDelete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": apiKey,
        },
        body: JSON.stringify({ ids: ids }),
    })
        .then((res) => res.json())
        .then((envelope) => {
            if (!envelope.status) {
                console.error("Bulk delete failed entirely:", envelope);
                alert(
                    `Could not delete items: ${envelope.error || "Unknown error"}`
                );
                return false;
            }

            envelope.data
                .filter((item) => item.status === true)
                .map((item) => item.data) // 'data' holds the ID
                .forEach((id) => downloadsTable.deleteEntries(id));

            const failedCount = envelope.data.filter(
                (item) => item.status === false
            ).length;

            if (failedCount > 0) {
                alert(`Could not delete ${failedCount} items.`);
                console.error("Deletion Response:", envelope);
            }

            downloadsTable.isSelected = false;

            return failedCount === 0;
        })
        .catch((err) => {
            alert(`Could not delete items: ${err}.`);
            console.error("Network or server error:", err);
            return false;
        });
}

function showTableInfo() {
    console.log(downloadsTable.getStatsString());
}

// SSE handles

function handleDeletes(payload) {
    downloadsTable.deleteEntries(payload.ids);
}

function handleUpdates(payload) {
    const entry = downloadsTable.entryMap.get(payload.id);
    if (entry === undefined) {
        console.warn(
            `Entry ${payload.id} could not be updated. Reason: not found.`
        );
        return;
    }

    entry.update(payload);
}

function handleProgress(payload) {
    const percentage = Math.round((payload.current / payload.total) * 100);
    payload.percentage = percentage;
    console.log("Progress update: ", payload);
}

// MAIN

const apiKey = window.MEDIA_SERVER_KEY;

const downloadsTableContainer = document.getElementById("downloadsTable");
const downloadsTable = new DownloadsTable(downloadsTableContainer);
window.downloadsTable = downloadsTable;

document.addEventListener("DOMContentLoaded", () => {
    handleColorScheme();

    fetch("/api/downloads", {
        headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
    })
        .then((response) => response.json())
        .then((data) => {
            downloadsTable.add(data);
        });

    // SSE Listener
    const stream = new StreamManager(`/api/events?apiKey=${apiKey}`);
    stream.connect(({ type, data }) => {
        switch (type) {
            case EVENT_TYPE.CREATE:
                downloadsTable.add(data);
                break;

            case EVENT_TYPE.UPDATE:
                handleUpdates(data);
                break;

            case EVENT_TYPE.PROGRESS:
                handleProgress(data);
                break;

            case EVENT_TYPE.DELETE:
                handleDeletes(data);
                break;

            default:
                console.warn(`Unhandled EventType received: ${type}`);
        }
    });

    window.bulkDelete = bulkDelete;
    window.filterTable = filterTable;
    window.clearSearch = clearSearch;
    window.showTableInfo = showTableInfo;
});
