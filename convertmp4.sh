#!/bin/bash

MOVIE_DIR="/home/senjo/movies"

find "$MOVIE_DIR" -type f \( \
    -iname "*.mkv" -o \
    -iname "*.avi" -o \
    -iname "*.mov" -o \
    -iname "*.webm" -o \
    -iname "*.flv" -o \
    -iname "*.wmv" \
\) | while read -r file; do

    output="${file%.*}.mp4"

    echo "Converting: $file"

    ffmpeg -i "$file" \
        -c:v libx264 -preset veryfast -crf 23 \
        -c:a aac -b:a 128k \
        -movflags +faststart \
        "$output"

    if [ $? -eq 0 ]; then
        echo "Success: $file -> $output"
        rm "$file"
    else
        echo "Failed: $file"
        rm -f "$output"
    fi

done

echo "All conversions finished."