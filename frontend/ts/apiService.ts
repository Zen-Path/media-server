import { API_SECRET_KEY } from "./constants";

/**
 * Fetches the list of downloads from the API.
 * @returns The JSON response payload.
 */
export async function fetchDownloads(): Promise<object> {
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
 * @param ids - An array of download IDs to delete.
 * @returns The JSON response payload.
 */
export async function deleteDownloads(ids: Array<number>): Promise<object> {
    try {
        const response = await fetch("/api/downloads", {
            method: "DELETE",
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
