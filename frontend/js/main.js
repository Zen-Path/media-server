import { EVENT_TYPE, API_SECRET_KEY } from "./constants.js";
import { handleColorScheme, debounce, StreamManager } from "./utils.js";
import { DownloadsTable } from "./downloadsTable.js";
import { showToast } from "./utils.js";
import Swal from "sweetalert2";

import "../css/main.css";
import "../css/dashboard.css";

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

async function bulkDelete(ids) {
    if (ids.length === 0) {
        showToast("No entries selected or visible to delete.", "warning");
        return false;
    }

    const result = await Swal.fire({
        title: "Are you sure?",
        text: `You are about to delete ${ids.length} entries. This cannot be undone.`,
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Yes, delete them!",
    });

    if (!result.isConfirmed) {
        return false;
    }

    const unique_ids = [...new Set(ids)];

    fetch("/api/bulkDelete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": API_SECRET_KEY,
        },
        body: JSON.stringify({ ids: unique_ids }),
    })
        .then((res) => res.json())
        .then((payload) => {
            if (!payload.status) {
                console.error("Bulk delete failed entirely:", payload);
                showToast(
                    `Could not delete entries: ${payload.error || "Unknown error"}`,
                    "error"
                );
                return false;
            }

            downloadsTable.deleteEntries(payload.data.ids);
            showToast(
                `Successfully deleted ${payload.data.ids.length} entries.`,
                "success"
            );

            const countDiff = unique_ids.length - payload.data.ids.length;
            if (countDiff > 0) {
                console.warn(`Failed to delete ${countDiff} entries.`);
                showToast(`Could not delete ${countDiff} entries.`, "warning");
            }

            return true;
        })
        .catch((err) => {
            showToast(`Could not delete entries: ${err}.`, "error");
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
    payload.forEach((entryData) => {
        const entry = downloadsTable.entryMap.get(entryData.id);
        if (entry === undefined) {
            console.warn(
                `Entry ${entryData.id} could not be updated. Reason: not found.`
            );
            return;
        }

        entry.update(entryData);
    });
}

// MAIN

const downloadsTableContainer = document.getElementById("downloadsTable");
const downloadsTable = new DownloadsTable(downloadsTableContainer);
window.downloadsTable = downloadsTable;

document.addEventListener("DOMContentLoaded", () => {
    handleColorScheme();

    fetch("/api/downloads", {
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": API_SECRET_KEY,
        },
    })
        .then((response) => response.json())
        .then((payload) => {
            downloadsTable.add(payload.data);
        });

    // SSE Listener
    const stream = new StreamManager(`/api/events?apiKey=${API_SECRET_KEY}`);
    stream.connect(({ type, data }) => {
        switch (type) {
            case EVENT_TYPE.CREATE:
                downloadsTable.add(data);
                break;

            case EVENT_TYPE.UPDATE:
                handleUpdates(data);
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
