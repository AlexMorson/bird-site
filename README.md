# Bird Site

Live online leaderboards, user profiles and rankings for The King's Bird.

## Quickstart

```
# Generate CSS
lessc bird/static/style.less bird/static/style.css

# Generate WebP images
./bird/optimise-backgrounds.sh

# Run debug server
uv run -m bird.leaderboards init
uv run flask --app bird.wsgi run --debug
```
