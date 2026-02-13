import { deleteDownloads } from "./apiService";
import { showToast } from "./utils";
import Swal from "sweetalert2";

export async function handleBulkDelete(ids: number[]) {
    if (!ids || ids.length === 0) {
        return showToast("No entries provided to delete.", "warning");
    }

    const uniqueIds = [...new Set(ids)];

    const isSingle = uniqueIds.length === 1;
    const itemText = isSingle
        ? `entry #${uniqueIds[0]}`
        : `${uniqueIds.length} entries`;

    const { isConfirmed } = await Swal.fire({
        title: "Are you sure?",
        text: `You are about to delete ${itemText}. This cannot be undone.`,
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Yes, delete them!",
    });

    if (!isConfirmed) return false;

    try {
        const payload = await deleteDownloads(uniqueIds);

        if (!payload.status) {
            console.error("Delete failed:", payload);
            showToast(
                `Could not delete ${isSingle ? "entry" : "entries"}.`,
                "error"
            );
            return false;
        }

        if (!payload.data?.ids) {
            console.error(
                "Field 'ids' is missing from downloads delete response."
            );
        }

        // Fallback to uniqueIds if server response is malformed
        const idsToDelete = payload.data?.ids || uniqueIds;

        // TODO: use deleteEntries result to provide an accurate report to the user
        // about what was and wasn't deleted.
        downloadsTable.deleteEntries(idsToDelete);
        const deletedCount = idsToDelete.length;

        // Report
        const requestedCount = uniqueIds.length;
        const missingCount = requestedCount - deletedCount;

        if (missingCount > 0) {
            console.warn(
                "Requested deletion of: ",
                uniqueIds,
                `, but only removed ${deletedCount} entries.`
            );

            const missingCountText =
                missingCount > 0 ? ` (${missingCount} not deleted` : "";
            showToast(
                `Deleted ${deletedCount}/${uniqueIds.length} entries${missingCountText}.`,
                "warning"
            );
        } else {
            showToast(
                `Successfully deleted ${deletedCount} ${deletedCount === 1 ? "entry" : "entries"}.`,
                "success"
            );
        }
    } catch (error) {
        console.error("Bulk delete error:", error);
        showToast("Network error occurred while deleting.", "error");
    }
}
