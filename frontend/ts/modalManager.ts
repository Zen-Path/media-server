import {
    MEDIA_TYPE_CONFIG,
    STATUS_CONFIG,
    API_SECRET_KEY,
    API_DOWNLOADS,
} from "./constants";
import { showToast } from "./utils";

export const ModalManager = {
    dom: {},

    /**
     * @param {Array|Object} entries - Single entry object or Array of entry objects
     */
    openEdit(entries) {
        const items = Array.isArray(entries) ? entries : [entries];
        if (items.length === 0) {
            showToast("No entries selected or visible to edit.", "warning");
            return;
        }

        const isBulk = items.length > 1;
        this._ensureModalExists();

        this.dom.title.textContent = isBulk
            ? `Bulk Edit (${items.length} items)`
            : "Edit Download";

        this.dom.form.innerHTML = "";

        // Title field (only for single edit)
        if (!isBulk) {
            this.dom.form.appendChild(
                this._createField(
                    "Title",
                    "text",
                    "editTitle",
                    items[0].data.title
                )
            );
        }

        const mediaTypeValue = isBulk ? "" : (items[0].data.mediaType ?? "");
        this.dom.form.appendChild(
            this._createSelectField(
                "Media Type",
                "editMediaType",
                MEDIA_TYPE_CONFIG,
                mediaTypeValue
            )
        );

        const statusValue = isBulk ? "" : (items[0].data.status ?? "");

        // Don't allow the user to set the status to unknown, that is just for the UI
        const { UNKNOWN, ...validStatusConfig } =
            structuredClone(STATUS_CONFIG);
        this.dom.form.appendChild(
            this._createSelectField(
                "Status",
                "editStatus",
                validStatusConfig,
                statusValue
            )
        );

        // Store the targets for the save function
        this.currentTargets = items.map((item) => item.data.id);

        this.dom.modal.classList.add("active");
    },

    async save() {
        const isBulk = this.currentTargets.length > 1;

        const payload = this.currentTargets.map((id) => {
            const data = { id };
            const typeVal = document.getElementById("editMediaType").value;
            const statusVal = document.getElementById("editStatus").value;

            if (typeVal !== "") data.mediaType = parseInt(typeVal);
            if (statusVal !== "") data.status = parseInt(statusVal);

            // Only add title if it's a single edit
            if (!isBulk) {
                data.title = document.getElementById("editTitle").value;
            }

            return data;
        });

        try {
            const res = await fetch(API_DOWNLOADS, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": API_SECRET_KEY,
                },
                body: JSON.stringify(payload),
            });

            if (res.ok) {
                payload.forEach((item) => {
                    const entry = window.downloadsTable.entryMap.get(item.id);
                    if (!entry) console.warn(`Item not updated: ${item}`);
                    entry.update(item);
                });
                this.close();
            }
        } catch (err) {
            console.error("Save failed:", err);
        }
    },

    _createField(label, type, id, value) {
        const group = document.createElement("div");
        group.className = "form-group";
        group.innerHTML = `
            <label for="${id}">${label}</label>
            <input type="${type}" id="${id}" value="${value || ""}" class="form-control">
        `;
        return group;
    },

    _createSelectField(label, id, config, currentValue) {
        const group = document.createElement("div");
        group.className = "form-group";
        const options = Object.entries(config)
            .map(
                ([val, cfg]) =>
                    `<option value="${val}" ${val == currentValue ? "selected" : ""}>${cfg.label}</option>`
            )
            .join("");

        group.innerHTML = `
            <label for="${id}">${label}</label>
            <select id="${id}" class="form-control">
                <option value="">-- Keep Original --</option>
                ${options}
            </select>
        `;
        return group;
    },

    _ensureModalExists() {
        if (this.dom.modal) return;

        const html = `
            <div id="editModal" class="modal-overlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="modalTitle">Edit</h3>
                        <button class="close-btn">&times;</button>
                    </div>
                    <div id="modalForm" class="modal-body"></div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary cancel-btn">Cancel</button>
                        <button class="btn btn-primary save-btn">Save Changes</button>
                    </div>
                </div>
            </div>`;

        document.body.insertAdjacentHTML("beforeend", html);

        this.dom = {
            modal: document.getElementById("editModal"),
            title: document.getElementById("modalTitle"),
            form: document.getElementById("modalForm"),
        };

        this.dom.modal.querySelector(".save-btn").onclick = () => this.save();
        this.dom.modal.querySelector(".cancel-btn").onclick = () =>
            this.close();
        this.dom.modal.querySelector(".close-btn").onclick = () => this.close();
    },

    close() {
        this.dom.modal.classList.remove("active");
    },
};
