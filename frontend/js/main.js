import { EVENT_TYPE, API_SECRET_KEY } from "./constants.js";
import { handleColorScheme, debounce, StreamManager } from "./utils.js";
import { DownloadsTable } from "./downloadsTable.js";
import { fetchDownloads } from "./apiService.js";

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

function showTableInfo() {
    console.log(downloadsTable.getStatsString());
}

async function loadTableData() {
    try {
        const payload = await fetchDownloads();
        downloadsTable.add(payload.data);
    } catch (error) {}
}

// SSE handles

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

    loadTableData();

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
                downloadsTable.deleteEntries(data.ids);
                break;

            default:
                console.warn(`Unhandled EventType received: ${type}`);
        }
    });

    window.filterTable = filterTable;
    window.clearSearch = clearSearch;
    window.showTableInfo = showTableInfo;
});
