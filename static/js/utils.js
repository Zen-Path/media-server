/**
 * Copies text to clipboard with fallback and returns success status.
 * @param {any} data
 * @returns {Promise<boolean>}
 */
export async function copyToClipboard(data) {
    // Convert everything to a string
    let text;

    // Handle Object/Array serialization
    if (typeof data === "object" && data !== null) {
        try {
            text = JSON.stringify(data, null, 4);
        } catch (e) {
            console.error("Failed to stringify object for clipboard", e);
            return false;
        }
    } else {
        // Handle strings, numbers, and null/undefined
        text = String(data ?? "");
    }

    if (!text) return false;

    // Modern API
    if (navigator.clipboard && window.isSecureContext) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.warn("Navigator clipboard failed:", err);
        }
    }
}

const DATE_FORMATTER = new Intl.DateTimeFormat("sv-SE", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
});

/**
 * Formats a Unix timestamp (seconds) to YYYY-MM-DD HH:mm:ss
 * Returns "-" if the input is null or invalid.
 */
export function toLocalStandardTime(timestamp) {
    if (typeof timestamp !== "number") return "-";

    // Convert seconds to milliseconds
    const date = new Date(timestamp * 1000);

    if (isNaN(date.getTime())) {
        console.warn(`Invalid timestamp provided: "${timestamp}"`);
        return "-";
    }

    return DATE_FORMATTER.format(date);
}

export function formatDuration(ms) {
    if (!ms || isNaN(ms)) return "0s";

    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
}

export function debounce(func, delay = 250) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => func.apply(this, args), delay);
    };
}

export function handleColorScheme() {
    const themeToggleBtn = document.getElementById("themeToggle");
    const themeIcon = themeToggleBtn.querySelector("i");

    // Check LocalStorage or System Preference on Load
    const currentTheme = localStorage.getItem("theme");
    const systemPrefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)"
    ).matches;

    if (currentTheme === "dark" || (!currentTheme && systemPrefersDark)) {
        document.body.classList.add("dark-mode");
        themeIcon.classList.replace("fa-moon", "fa-sun"); // Change icon if needed
    }

    themeToggleBtn.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");

        let theme = "light";

        // If dark mode is now active
        if (document.body.classList.contains("dark-mode")) {
            theme = "dark";
            themeIcon.classList.replace("fa-moon", "fa-sun");
        } else {
            themeIcon.classList.replace("fa-sun", "fa-moon");
        }

        themeToggleBtn.title = `Toggle ${theme === "dark" ? "Light" : "Dark"} Mode`;

        // Save preference to localStorage
        localStorage.setItem("theme", theme);
    });
}

/**
 * Generates a standardized Icon + Label container.
 * @param {Object} options - Configuration for the pair.
 * @param {string} options.icon - Space-separated FontAwesome classes (e.g., "fa-clock").
 * @param {string} options.label - The text to display.
 * @param {Array<string>} [options.extraClasses] - Additional classes for the container.
 * @param {string} [options.title] - Optional tooltip.
 * @returns {HTMLElement}
 */
export function createIconLabelPair({
    icon,
    label,
    extraClasses = [],
    title = "",
}) {
    const container = document.createElement("div");
    container.classList.add("icon-label-group", ...extraClasses);
    if (title) container.title = title;

    const iconEl = document.createElement("i");
    // Handle split for multiple classes (like "fa-spinner fa-spin")
    iconEl.classList.add("fa-solid", ...icon.split(" "));

    const labelEl = document.createElement("span");
    labelEl.classList.add("label", "truncate");
    labelEl.textContent = label;

    container.append(iconEl, labelEl);
    return container;
}

export class StreamManager {
    constructor(url) {
        this.url = url;
        this.source = null;
    }

    connect(onUpdate) {
        this.source = new EventSource(this.url);

        this.source.onmessage = (event) => {
            const payload = JSON.parse(event.data);
            onUpdate(payload);
        };

        window.addEventListener("beforeunload", () => this.disconnect());
    }

    disconnect() {
        if (this.source) {
            this.source.close();
            this.source = null;
            console.log("Stream disconnected.");
        }
    }
}
