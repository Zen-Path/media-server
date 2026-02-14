import { MEDIA_TYPE } from "../../shared/constants";

interface FormResult {
    urls: string[];
    mediaType: number | null;
    rangeStart: number | null;
    rangeEnd: number | null;
}

export class DownloadFormGenerator {
    private readonly OVERLAY_ID = "gm-url-extractor-overlay";
    private cssStyleStr: string;
    private styleElement: HTMLStyleElement | null = null;
    private overlay: HTMLElement | null = null;

    // UI References
    private urlInput!: HTMLTextAreaElement;
    private urlLog!: HTMLDivElement;
    private mediaSelect!: HTMLSelectElement;
    private rangeStart!: HTMLInputElement;
    private rangeEnd!: HTMLInputElement;
    private rangeLog!: HTMLDivElement;
    private submitBtn!: HTMLButtonElement;

    constructor(cssStyleStr: string) {
        this.cssStyleStr = cssStyleStr;
    }

    /**
     * Opens the overlay and returns a Promise that resolves when
     * the user submits (with data) or cancels (null).
     */
    public open(): Promise<FormResult | null> {
        // Prevent multiple overlays
        if (document.getElementById(this.OVERLAY_ID)) {
            return Promise.resolve(null);
        }

        return new Promise<FormResult | null>((resolve) => {
            this.render(resolve);
        });
    }

    /**
     * Closes the overlay and cleans up the DOM.
     */
    public close(): void {
        if (this.overlay) {
            this.overlay.remove();
            this.overlay = null;
        }
        if (this.styleElement) {
            this.styleElement.remove();
            this.styleElement = null;
        }
    }

    private render(resolve: (value: FormResult | null) => void): void {
        this.styleElement = GM_addStyle(this.cssStyleStr);

        this.overlay = GM_addElement(document.body, "div", {
            id: this.OVERLAY_ID,
        });

        const container = document.createElement("div");
        container.className = "gm-overlay-box";
        this.overlay!.appendChild(container);

        // Header
        const title = document.createElement("div");
        title.className = "gm-overlay-title";
        title.textContent = "URL Extractor";
        container.appendChild(title);

        // URL Input
        const urlSection = document.createElement("div");

        const urlLabel = document.createElement("label");
        urlLabel.className = "gm-label";
        urlLabel.textContent = "Paste URLs (One per line)";

        this.urlInput = document.createElement("textarea");
        this.urlInput.className = "gm-textarea";
        this.urlInput.placeholder = "https://...";
        this.urlInput.value = window.location.href; // Default value

        this.urlLog = document.createElement("div");
        this.urlLog.id = "gm-url-log";
        this.urlLog.className = "gm-log";
        this.urlLog.textContent = "Found 0 valid URLs";

        urlSection.append(urlLabel, this.urlInput, this.urlLog);
        container.appendChild(urlSection);

        // Media Type
        const mediaSection = document.createElement("div");

        const mediaLabel = document.createElement("label");
        mediaLabel.className = "gm-label";
        mediaLabel.textContent = "Media Type";

        this.mediaSelect = this.createMediaSelect(MEDIA_TYPE.GALLERY);

        mediaSection.append(mediaLabel, this.mediaSelect);
        container.appendChild(mediaSection);

        // Range
        const rangeSection = document.createElement("div");

        const rangeLabel = document.createElement("label");
        rangeLabel.className = "gm-label";
        rangeLabel.textContent = "Range (Start : End)";

        const rangeRow = document.createElement("div");
        rangeRow.className = "gm-row";

        this.rangeStart = document.createElement("input");
        this.rangeStart.type = "number";
        this.rangeStart.className = "gm-input";
        this.rangeStart.placeholder = "Start";

        const separator = document.createElement("span");
        separator.style.fontWeight = "bold";
        separator.textContent = ":";

        this.rangeEnd = document.createElement("input");
        this.rangeEnd.type = "number";
        this.rangeEnd.className = "gm-input";
        this.rangeEnd.placeholder = "End";

        this.rangeLog = document.createElement("div");
        this.rangeLog.id = "gm-range-log";
        this.rangeLog.className = "gm-log";

        rangeRow.append(
            this.rangeStart,
            separator,
            this.rangeEnd,
            this.rangeLog
        );
        rangeSection.append(rangeLabel, rangeRow);
        container.appendChild(rangeSection);

        // Actions
        const actionSection = document.createElement("div");
        actionSection.className = "gm-actions";

        const btnCancel = document.createElement("button");
        btnCancel.className = "gm-btn gm-btn-cancel";
        btnCancel.textContent = "Cancel";

        this.submitBtn = document.createElement("button");
        this.submitBtn.className = "gm-btn gm-btn-submit";
        this.submitBtn.textContent = "Submit";

        actionSection.append(btnCancel, this.submitBtn);
        container.appendChild(actionSection);

        this.bindEvents(resolve, btnCancel);

        // Trigger initial validation for the default value
        this.validateUrls();
    }

    private createMediaSelect(defaultId: number): HTMLSelectElement {
        const select = document.createElement("select");
        select.id = "gm-media-select";
        select.className = "gm-select";

        Object.entries(MEDIA_TYPE).forEach(([name, value]) => {
            const option = document.createElement("option");
            option.value = String(value);
            // Convert "GALLERY" -> "Gallery"
            option.textContent = name.charAt(0) + name.slice(1).toLowerCase();

            if (value === defaultId) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        // Add "Unknown" option manually
        const unknownOpt = document.createElement("option");
        unknownOpt.value = "";
        unknownOpt.textContent = "Unknown";
        select.appendChild(unknownOpt);

        return select;
    }

    private bindEvents(
        resolve: (val: FormResult | null) => void,
        btnCancel: HTMLButtonElement
    ) {
        // Live validation
        this.urlInput.addEventListener("input", () => this.validateUrls());
        this.rangeStart.addEventListener("focusout", () => this.validateUrls());
        this.rangeEnd.addEventListener("focusout", () => this.validateUrls());

        this.rangeEnd.addEventListener("input", () => {
            this.rangeEnd.classList.remove("gm-error");
        });

        // Cancel
        btnCancel.addEventListener("click", () => {
            this.close();
            resolve(null);
        });

        // Submit
        this.submitBtn.addEventListener("click", () => {
            const result = this.handleSubmission();
            if (result) {
                this.close();
                resolve(result);
            }
        });
    }

    private validateUrls(): void {
        const text = this.urlInput.value;
        const lines = text
            .split("\n")
            .map((l) => l.trim())
            .filter((l) => l !== "");

        let validCount = 0;
        let invalidCount = 0;

        lines.forEach((line) => {
            try {
                new URL(line); // Will throw if invalid
                validCount++;
            } catch (e) {
                invalidCount++;
            }
        });

        if (invalidCount > 0) {
            this.urlLog.textContent = `Found ${validCount} valid URLs. (${invalidCount} invalid)`;
            this.urlLog.style.color = "#ff4444";
            // this.submitBtn.disabled = true;
        } else {
            this.urlLog.textContent = `Found ${validCount} valid URLs`;
            this.urlLog.style.color = "";
            // this.submitBtn.disabled = false;
        }
    }

    private validateRange() {
        const startVal =
            this.rangeStart.value.trim() !== ""
                ? parseInt(this.rangeStart.value)
                : null;
        const endVal =
            this.rangeEnd.value.trim() !== ""
                ? parseInt(this.rangeEnd.value)
                : null;

        if (startVal !== null && endVal !== null && startVal > endVal) {
            this.rangeEnd.classList.add("gm-error");
            this.rangeLog.textContent =
                "Start value cannot be greater than End value";
        }

        return [startVal, endVal];
    }

    private handleSubmission(): FormResult | null {
        const rawUrls = this.urlInput.value
            .split("\n")
            .map((l) => l.trim())
            .filter((l) => l !== "");

        const validUrls = rawUrls.filter((url) => {
            try {
                return new URL(url);
            } catch {
                return false;
            }
        });

        const mediaType =
            this.mediaSelect.value.trim() !== ""
                ? parseInt(this.mediaSelect.value)
                : null;

        const [rangeStart, rangeEnd] = this.validateRange();

        return {
            urls: validUrls,
            mediaType,
            rangeStart,
            rangeEnd,
        };
    }
}
