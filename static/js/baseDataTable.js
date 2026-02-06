import { copyToClipboard, createIconLabelPair } from "./utils.js";

export class BaseDataTable {
    constructor(container) {
        if (!container) throw new Error("A container element is required.");

        this.entryMap = new Map();
        this.entryList = [];

        this.dom = {
            container,
            header: null,
            body: null,
            selectAll: null,
            sortIndicators: new Map(),
        };

        this.lastSort = { field: null, direction: null };
        this.isSorted = false;

        this.columnsMap = {};
        this.columnsList = [];

        this.selectedCount = 0;

        this.lastSelectedIndex = null;
    }

    init() {
        this.dom.container.innerHTML = "";

        const tableWrapper = document.createElement("div");
        tableWrapper.className = "data-table-wrapper";

        this.dom.header = this.#buildHeader();
        this.dom.body = document.createElement("div");
        this.dom.body.className = "data-table-body";

        tableWrapper.append(this.dom.header, this.dom.body);
        this.dom.container.append(tableWrapper);
    }

    _addEntries(entriesData, RowClass, tableRef) {
        console.log(entriesData);
        const fragment = document.createDocumentFragment();

        const isFirstCall = this.entryList.length === 0;

        for (const entryData of entriesData) {
            try {
                const id = entryData?.id;
                if (typeof id !== "number") {
                    console.error("ID is missing or invalid:", id, entryData);
                    continue;
                }

                if (this.entryMap.has(id)) continue;

                const entry = new RowClass(entryData, tableRef);

                this.entryMap.set(id, entry);
                this.entryList.unshift(entry);

                const rowEl = entry.render();

                // Handle animations
                if (!isFirstCall) {
                    rowEl.classList.add("row-fade-in");
                    rowEl.addEventListener(
                        "animationend",
                        () => {
                            rowEl.classList.remove("row-fade-in");
                        },
                        { once: true }
                    );
                }

                if (isFirstCall) {
                    fragment.append(rowEl);
                } else {
                    // New entries should be added to the top of the table
                    fragment.prepend(rowEl);
                }
            } catch (error) {
                console.error(`Couldn't add entry ${entry?.id}:`, error);
            }
        }

        if (this.dom.body) {
            this.dom.body.prepend(fragment);
        }

        this.isSorted = false;
    }

    #buildHeader() {
        const headerRow = document.createElement("div");
        headerRow.className = "data-table-header";

        this.columnsList.forEach((column) => {
            const cell = document.createElement("div");
            cell.className = `header-cell ${column.cssClass || ""}`;

            switch (column.id) {
                case this.columnsMap.CHECKBOX.id:
                    this.dom.selectAll = this.#createCheckbox();
                    cell.appendChild(this.dom.selectAll);
                    break;
                case this.columnsMap.ACTIONS.id:
                    cell.appendChild(this._createActions());
                    break;
                default:
                    cell.append(
                        createIconLabelPair({
                            icon: column.icon,
                            label: column.label,
                            title: column.label,
                        })
                    );
                    break;
            }

            if (column.sortable && column.field) {
                cell.classList.add("sortable");
                cell.onclick = () => this.handleSortClick(column.field);

                const icon = document.createElement("i");
                icon.className = "fa-solid sort-indicator";

                this.dom.sortIndicators.set(column.field, icon);
                cell.appendChild(icon);
            }

            headerRow.appendChild(cell);
        });

        return headerRow;
    }

    #createCheckbox() {
        const input = document.createElement("input");
        input.type = "checkbox";
        input.checked = this.isSelected;

        input.onclick = (e) => {
            // Stop the event from reaching the sortable header cell
            e.stopPropagation();

            this.toggleAll(e.target.checked);
        };

        return input;
    }

    _createActions() {
        throw new Error("Implement 'initData'.");
    }

    // UTILS

    getVisibleEntries() {
        return this.entryList.filter((entry) => entry.isVisible);
    }

    getSelectedEntries() {
        return this.entryList.filter((entry) => entry.isSelected);
    }

    #updateSortIndicators() {
        const { field, direction } = this.lastSort;

        this.dom.sortIndicators.forEach((indicator, indicatorField) => {
            if (indicatorField === field) {
                indicator.classList.remove("fa-caret-up", "fa-caret-down");
                indicator.classList.add(
                    direction === 1 ? "fa-caret-up" : "fa-caret-down",
                    "active"
                );
            } else {
                indicator.classList.remove(
                    "active",
                    "fa-caret-up",
                    "fa-caret-down"
                );
            }
        });
    }

    // PUBLIC

    sort(field, direction = 1) {
        console.log(
            `Sorting by ${field} in ${direction === 1 ? "asc" : "desc"} order.`,
            direction
        );

        this.entryList.sort((a, b) => {
            const valA = a.sortValues[field];
            const valB = b.sortValues[field];

            if (valA === valB) return 0;
            const order = valA > valB ? 1 : -1;

            return order * direction;
        });

        // Batch update DOM
        const fragment = document.createDocumentFragment();
        this.entryList.forEach((entry) => fragment.appendChild(entry.dom.row));
        this.dom.body.appendChild(fragment);

        this.lastSort = { field, direction };
        this.isSorted = true;
        this.#updateSortIndicators();
    }

    handleSortClick(field) {
        const newDirection =
            this.lastSort.field === field && this.lastSort.direction === 1
                ? -1
                : 1;
        this.sort(field, newDirection);
    }

    filter(searchValue) {
        const query = String(searchValue).trim().toLowerCase();

        requestAnimationFrame(() => {
            this.entryList.forEach((entry) => {
                if (query === "") {
                    entry.isVisible = true;
                    return;
                }

                const matches = entry.searchIndex.includes(query);
                entry.isVisible = matches;
            });
        });
    }

    deleteEntries(ids) {
        const idList = Array.isArray(ids) ? ids : [ids];
        if (idList.length === 0) return;

        requestAnimationFrame(() => {
            let selectionChanged = false;

            idList.forEach((id) => {
                const entry = this.entryMap.get(id);

                if (!entry) {
                    console.warn(
                        `Item #${id} could not be deleted: not found.`
                    );
                    return;
                }

                // Update selection count if necessary
                if (entry.isSelected) {
                    this.selectedCount = Math.max(0, this.selectedCount - 1);
                    selectionChanged = true;
                }

                entry.remove();

                this.entryMap.delete(id);
            });

            this.entryList = this.entryList.filter((entry) =>
                this.entryMap.has(entry.data.id)
            );

            this.updateHeaderCheckbox();
        });
    }

    async copyFields(field, unique = true) {
        const processableItems = this.getSelectedEntries();
        if (processableItems.length === 0) return false;

        const data = processableItems.map((entry) => entry.data[field]);
        const finalData = unique ? [...new Set(data)] : data;
        const finalDataStr = finalData.join("\n");

        return await copyToClipboard(finalDataStr);
    }

    toggleAll(checked) {
        this.getVisibleEntries().forEach((entry) => {
            entry.isSelected = checked;
        });
    }

    updateHeaderCheckbox() {
        const selectAll = this.dom.selectAll;
        if (!selectAll) return;

        const total = this.entryList.length;
        const selected = this.selectedCount;

        if (selected === 0) {
            selectAll.checked = false;
            selectAll.indeterminate = false;
        } else if (selected === total) {
            selectAll.checked = true;
            selectAll.indeterminate = false;
        } else {
            selectAll.checked = false;
            selectAll.indeterminate = true;
        }
    }
}

export class BaseDataRow {
    constructor(data, table) {
        this.data = structuredClone(data);
        this.table = table;

        this.dom = { row: null };

        // Storage for pre-calculated values
        this.sortValues = {};
        this.displayValues = {};
        this.searchIndex = "";

        // State
        this._isSelected = false;
        this._isVisible = true;
    }

    get isSelected() {
        return this._isSelected;
    }

    set isSelected(value) {
        if (this._isSelected === value) return;
        this._isSelected = value;

        if (this.dom.checkbox) this.dom.checkbox.checked = value;
        this.sortValues.isSelected = value;

        this.table.selectedCount += value ? 1 : -1;
        this.table.updateHeaderCheckbox();
    }

    get isVisible() {
        return this._isVisible;
    }

    set isVisible(value) {
        if (this._isVisible === value) return;
        this._isVisible = value;
        if (this.dom.row) this.dom.row.classList.toggle("hidden", !value);
    }

    initData() {
        throw new Error("Implement 'initData'.");
    }

    render() {
        throw new Error("Implement 'render'.");
    }

    update() {
        throw new Error("Implement 'update'.");
    }

    remove() {
        if (this.dom.row) this.dom.row.remove();
        this.dom = null;
    }
}
