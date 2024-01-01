#!/bin/sh

BIRD_DIR=$(dirname "$(realpath "$0")")
BACKGROUNDS_DIR="$BIRD_DIR/static/backgrounds"

for input in "$BACKGROUNDS_DIR"/*.png; do
    cwebp -m 6 -resize 1280 720 -q 30 "$input" -o "${input%.*}.webp"
done
