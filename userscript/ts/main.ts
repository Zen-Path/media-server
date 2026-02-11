"use strict";

import { createDownloadForm } from "./createDownloadForm";
import { showDownloadStatus } from "./utils";
import {
    DOWNLOAD_STATUS,
    SERVER_PORT,
    API_SECRET_KEY,
} from "../../shared/constants";

import STYLES from "../css/style.css?inline";

const BASE_URL = `http://localhost:${SERVER_PORT}`;
const API_DOWNLOAD = `${BASE_URL}/api/media/download`;

interface DownloadPayload {
    urls: string[];
    mediaType?: number;
    rangeStart?: number;
    rangeEnd?: number;
}

interface MediaEntry {
    status: boolean;
    [key: string]: any; // Allows any other fields
}

function downloadMedia(
    urls: string[],
    mediaType?: number,
    rangeStart?: number,
    rangeEnd?: number
) {
    showDownloadStatus(DOWNLOAD_STATUS.IN_PROGRESS, false);

    if (!Array.isArray(urls) || urls.length === 0) {
        alert("Invalid or empty URLs array provided.");
        console.error("Invalid URLs: ", urls);
        return;
    }

    const payload: DownloadPayload = { urls, mediaType, rangeStart, rangeEnd };

    GM_xmlhttpRequest({
        method: "POST",
        url: API_DOWNLOAD,
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": API_SECRET_KEY,
        },
        data: JSON.stringify(payload),
        onload: function (response) {
            if (response.status < 200 || response.status > 300) {
                console.warn(":: Response info", response);
                showDownloadStatus(DOWNLOAD_STATUS.FAILED);
                return;
            }

            try {
                const responseData = JSON.parse(response.responseText);
                const entries = (responseData.data as MediaEntry[]) || [];

                console.log(":: Download response", responseData);

                if (!responseData.status || entries.length === 0) {
                    console.error(
                        "Download failed or empty response:",
                        responseData.error
                    );
                    showDownloadStatus(DOWNLOAD_STATUS.FAILED);
                    return;
                }

                const totalItems = entries.length;
                const successCount = entries.filter(
                    (data) => data.status === true
                ).length;

                let overallStatus;
                if (successCount === totalItems) {
                    overallStatus = DOWNLOAD_STATUS.DONE;
                } else if (successCount === 0) {
                    overallStatus = DOWNLOAD_STATUS.FAILED;
                } else {
                    overallStatus = DOWNLOAD_STATUS.MIXED;
                }

                showDownloadStatus(overallStatus);

                // Log failures for debugging
                if (successCount < totalItems) {
                    entries.forEach((data) => {
                        if (!data.status) {
                            console.error(
                                `Error for ${data.url}:`,
                                data.error || "Unknown error"
                            );
                        }
                    });
                }
            } catch (error) {
                console.error("Failed to parse server response", error);
                showDownloadStatus(DOWNLOAD_STATUS.FAILED);
            }
        },
        onerror: function (error) {
            console.error("Download failed", error);
            showDownloadStatus(DOWNLOAD_STATUS.FAILED);
        },
    });
}

function main() {
    GM_registerMenuCommand("Download Media", () => {
        const currentUrl = window.location.href;
        downloadMedia([currentUrl]);
    });

    GM_registerMenuCommand("Open Download Form", async () => {
        const formData = await createDownloadForm(STYLES);
        console.log("Download Form Data:", formData);

        if (!formData) return;

        downloadMedia(
            formData.urls,
            formData.mediaType,
            formData.rangeStart,
            formData.rangeEnd
        );
    });

    GM_registerMenuCommand("Open Dashboard", () => {
        // { active: true } ensures the new tab gets focus immediately
        GM_openInTab(`${BASE_URL}/dashboard`, { active: true });
    });
}

main();
