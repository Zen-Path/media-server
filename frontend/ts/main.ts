import { EVENT_TYPE, API_SECRET_KEY } from "./constants";
import { handleColorScheme, debounce, StreamManager, showToast } from "./utils";
import { DownloadsTable } from "./downloadsTable";
import { fetchDownloads } from "./apiService";

import { Grid, html } from "gridjs";

import "gridjs/dist/theme/mermaid.css";

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

const grid = new Grid({
    columns: [
        { id: "id", name: "ID" },
        { id: "mediaType", name: "Media Type" },
        {
            name: "Name",
            // We don't bind 'id' here because this is a composite column
            formatter: (_, row) => {
                console.log(_, row);
                // row.cells returns an array of ALL columns (even hidden ones)
                // Order matches the columns array below:
                // Index 0: Name (Current)
                // Index 1: Title (Hidden)
                // Index 2: URL (Hidden)

                const title = row.cells[3].data;
                const url = row.cells[4].data;

                return html(`
          <a href="${url}" target="_blank" style="display: flex; flex-direction: column; text-decoration: none;">
            <span class="title truncate" style="font-weight: bold; color: #333;" title="${title}">
                ${title}
            </span>
            <span class="url truncate" style="font-size: 0.85em; color: #888;" title="${url}">
                ${url}
            </span>
          </a>
        `);
            },
        },
        // HIDDEN COLUMNS (Essential for accessing the data)
        { id: "title", name: "Title", hidden: true },
        { id: "url", name: "URL", hidden: true },
        {
            id: "startTime",
            name: "Start Time",
            // Convert Unix timestamp (seconds) to readable date
            formatter: (cell) => new Date(cell * 1000).toLocaleString(),
        },
        {
            id: "status",
            name: "Status",
            // Optional: Map status codes to text
            formatter: (cell) =>
                cell === 3 ? "Done" : cell === 5 ? "Error" : "Pending",
        },
    ],

    // 2. Connect your async function here
    data: async () => {
        const response = await fetchDownloads();
        return response.data; // Grid.js needs the array, not the wrapper object
    },

    search: true,
    sort: true,
    pagination: {
        limit: 25,
    },
});
const wrapper = document.getElementById("wrapper");
if (wrapper) {
    grid.render(wrapper);
}

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
