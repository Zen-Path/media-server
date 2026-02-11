import { defineConfig } from "vite";
import monkey from "vite-plugin-monkey";
import fs from "node:fs";

// Extract project version from pyproject.toml (whilst not using a separate toml lib)
const pyprojectContent = fs.readFileSync("./pyproject.toml", "utf8");
const versionMatch = pyprojectContent.match(/version\s*=\s*["']([^"']+)["']/);
const version = versionMatch ? versionMatch[1] : "0.0.0";

export default defineConfig({
    plugins: [
        monkey({
            entry: "userscript/ts/main.ts",
            userscript: {
                name: "File Downloader",
                namespace: "Flexycon",
                match: ["*://*/*"],
                version: version,
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
