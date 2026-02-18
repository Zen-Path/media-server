"use strict";

import { DownloadFormGenerator } from "./createDownloadForm";
import { BASE_URL, downloadMedia } from "./apiService";
import { PAGE_DASHBOARD } from "../../shared/constants";

import STYLES from "../css/style.css?inline";

function main() {
    GM_registerMenuCommand("Download Media", () => {
        const currentUrl = window.location.href;
        downloadMedia([currentUrl]);
    });

    GM_registerMenuCommand("Open Download Form", async () => {
        const form = new DownloadFormGenerator(STYLES);
        const formData = await form.open();

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
        GM_openInTab(`${BASE_URL}${PAGE_DASHBOARD}`, { active: true });
    });
}

main();
