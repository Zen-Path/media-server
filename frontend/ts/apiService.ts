import { API_SECRET_KEY } from "./constants";

/**
 * Fetches the list of downloads from the API.
 * @returns {Promise<Object>} The JSON response payload.
 */
export async function fetchDownloads() {
    try {
        const response = await fetch("/api/downloads", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": API_SECRET_KEY,
            },
        });

        if (!response.ok) {
            throw new Error(
                `API Error: ${response.status} ${response.statusText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch downloads:", error);
        throw error;
    }
}

/**
 * Bulk deletes downloads by their IDs.
 * @param {Array<number>} ids - An array of download IDs to delete.
 * @returns {Promise<Object>} The JSON response payload.
 */
export async function deleteDownloads(ids) {
    try {
        const response = await fetch("/api/bulkDelete", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": API_SECRET_KEY,
            },
            body: JSON.stringify({ ids }),
        });

        if (!response.ok) {
            throw new Error(
                `API Error: ${response.status} ${response.statusText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to delete downloads:", error);
        throw error;
    }
}
