#!/bin/bash

# Define the target directory and output file
TARGET_DIR="."
OUTPUT_FILE="combined_output.txt"

# Empty the output file if it already exists
> "$OUTPUT_FILE"

# Find all files, excluding the output file itself
find "$TARGET_DIR" -type f ! -name "$OUTPUT_FILE" | while read -r file; do
    echo "# $file" >> "$OUTPUT_FILE"
    cat "$file" >> "$OUTPUT_FILE"
    echo -e "\n" >> "$OUTPUT_FILE"
done

echo "Done! All files have been merged into $OUTPUT_FILE"
