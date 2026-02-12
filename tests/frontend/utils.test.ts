import { describe, it, expect } from "vitest";
import { formatDuration } from "../../frontend/ts/utils";

describe("formatDuration()", () => {
    it("should handle small durations (seconds)", () => {
        expect(formatDuration(5000)).toBe("5s");
        expect(formatDuration(500)).toBe("0s"); // Rounds down
    });

    it("should format minutes correctly", () => {
        expect(formatDuration(65000)).toBe("1m 5s");
        expect(formatDuration(3599000)).toBe("59m 59s");
    });

    it("should format hours correctly and drop seconds", () => {
        // 1h 1m 5s -> should only show 1h 1m
        expect(formatDuration(3665000)).toBe("1h 1m");
    });

    it("should format days correctly and drop minutes/seconds", () => {
        // 1 day + 2 hours
        const ms = 24 * 60 * 60 * 1000 + 2 * 60 * 60 * 1000;
        expect(formatDuration(ms)).toBe("1d 2h");
    });

    it('should return "0s" for invalid or falsy inputs', () => {
        expect(formatDuration(null)).toBe("0s");
        expect(formatDuration(NaN)).toBe("0s");
        expect(formatDuration(0)).toBe("0s");
    });
});
