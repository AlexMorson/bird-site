#!/bin/sh

for input in static/backgrounds/*.png; do
    cwebp -m 6 -resize 1280 720 -q 30 "$input" -o "${input%.*}.webp"
done
