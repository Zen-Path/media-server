import { defineConfig } from "vite";
import monkey from "vite-plugin-monkey";

export default defineConfig({
    plugins: [
        monkey({
            entry: "userscript/main.js",
            userscript: {
                name: "File Downloader",
                namespace: "Flexycon",
                match: ["*://*/*"],
                version: "2.2.1",
                author: "Zen-Path",
                description:
                    "Send a download request for a URL to a local media server.",
                supportURL:
                    "https://github.com/Zen-Path/flexycon/tree/main/dotfiles/src/scripts/media_server",
                homepageURL: "https://github.com/Zen-Path/flexycon",
                icon: "https://www.svgrepo.com/show/230395/download.svg",
                grant: [
                    "GM_registerMenuCommand",
                    "GM_xmlhttpRequest",
                    "GM_openInTab",
                    "GM_addStyle",
                    "GM_addElement",
                ],
                noframes: true,
            },

            build: {
                fileName: "script.user.js",
            },
        }),
    ],
    build: {
        outDir: "userscript/dist",
        emptyOutDir: true,
    },
});
