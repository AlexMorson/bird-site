# Bird Site

Live online leaderboards, user profiles and rankings for The King's Bird.

## Quickstart

```
# Generate CSS
lessc bird/static/style.less bird/static/style.css

# Generate WebP images
./bird/optimise-backgrounds.sh

# Run debug server
poetry install --no-root
poetry shell
python -m bird.leaderboards init
flask --app bird.wsgi run --debug
```
