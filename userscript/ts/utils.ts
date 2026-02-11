import { DOWNLOAD_STATUS } from "../../shared/constants";

// prettier-ignore
const STATUS_ICONS = Object.freeze({
    [DOWNLOAD_STATUS.PENDING]:      "🔜",
    [DOWNLOAD_STATUS.IN_PROGRESS]:  "⏳",
    [DOWNLOAD_STATUS.DONE]:         "🟩",
    [DOWNLOAD_STATUS.FAILED]:       "🟥",
    [DOWNLOAD_STATUS.MIXED]:        "🟨",
})

let statusFlashTimer = null;

/**
 * Updates the document title with a status icon and optional flashing effect.
 *
 * After a short timer, the icon remains static.
 * @param {number} statusId - The ID from DOWNLOAD_STATUS
 * @param {boolean} [flash=false] - If true, the icon will flash to grab attention
 */
export function showDownloadStatus(statusId, flash = true) {
    // Clear existing flashers
    if (statusFlashTimer) {
        clearInterval(statusFlashTimer);
        statusFlashTimer = null;
    }

    const icon = STATUS_ICONS[statusId];
    if (icon && document.title.startsWith(`${icon} - `)) {
        return;
    }

    const allIcons = Object.values(STATUS_ICONS).join("");
    const statusRegex = new RegExp(`^[${allIcons}]\\s-\\s`, "u");
    const cleanTitle = document.title.replace(statusRegex, "");

    if (!icon) {
        document.title = cleanTitle;
        return;
    }

    const staticTitle = `${icon} - ${cleanTitle}`;
    if (!flash) {
        document.title = staticTitle;
        return;
    }

    // Start flashing
    let showIcon = true;
    statusFlashTimer = setInterval(() => {
        document.title = showIcon ? staticTitle : cleanTitle;
        showIcon = !showIcon;
    }, 500);

    // Auto-stop flashing
    setTimeout(() => {
        if (statusFlashTimer) {
            clearInterval(statusFlashTimer);
            statusFlashTimer = null;
            document.title = staticTitle;
        }
    }, 3000);
}
