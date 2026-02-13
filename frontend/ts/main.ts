import { EVENT_TYPE, API_SECRET_KEY } from "./constants";
import { handleColorScheme, debounce, StreamManager, showToast } from "./utils";
import { DownloadsTable } from "./downloadsTable";
import { fetchDownloads } from "./apiService";

import "../css/main.css";
import "../css/dashboard.css";

const debouncedFilter = debounce((searchValue: string) => {
    requestAnimationFrame(() => {
        downloadsTable.filter(searchValue);
    });
}, 10);

// Only starts filtering after a small delay
function filterTable() {
    const searchInput = document.getElementById(
        "searchInput"
    ) as HTMLInputElement | null;

    let searchValue = "";
    if (searchInput) {
        searchValue = searchInput.value;
    }

    const clearBtn = document.getElementById("clearBtn");
    if (clearBtn) {
        clearBtn.classList.toggle("show", searchValue.length > 0);
    }

    debouncedFilter(searchValue);
}

// Updates UI and filters the table instantly
function clearSearch() {
    const searchInput = document.getElementById(
        "searchInput"
    ) as HTMLInputElement | null;

    if (searchInput) {
        searchInput.value = "";
        searchInput.focus();
    }

    const clearBtn = document.getElementById(
        "clearBtn"
    ) as HTMLButtonElement | null;
    if (clearBtn) {
        clearBtn.classList.remove("show");
    }

    downloadsTable.filter("");
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

function refreshData() {
    // TODO: add a refreshData method to the data table
    loadTableData();
    showToast("Table data refreshed!", "success");
}

// SSE handles

function handleUpdates(payload: any[]) {
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

if (!downloadsTableContainer) {
    throw new Error("Required element #downloadsTable not found.");
}

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
    window.refreshData = refreshData;
    window.showTableInfo = showTableInfo;
});
