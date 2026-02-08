import { defineConfig } from "vite";
import path from "path";

export default defineConfig({
    // Where your source code lives
    root: path.resolve(__dirname, "frontend"),

    build: {
        outDir: path.resolve(__dirname, "app/static"),

        // Clear the destination folder before building
        emptyOutDir: true,

        // Do not randomize filenames (no hashing)
        rollupOptions: {
            input: path.resolve(__dirname, "frontend/js/main.js"),
            output: {
                entryFileNames: "bundle.js",
                assetFileNames: (assetInfo) => {
                    if (assetInfo.name.endsWith(".css")) {
                        return "style.css";
                    }
                    return "assets/[name][extname]";
                },
                format: "es", // Standard ES Module format
            },
        },

        // Turn off for production
        minify: false,
    },
});
