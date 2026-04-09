# Botany in a Day

A web-based plant family quiz inspired by Thomas Elpel's [*Botany in a Day*](https://hopspress.com/Books/Botany_in_a_Day.htm). Test your ability to identify the 8 starter plant families using real observation photos from [iNaturalist](https://www.inaturalist.org/).

## How It Works

Each quiz question fetches a random research-grade plant observation from iNaturalist (filtered to observations with flowering photos and open licenses). You pick which of the 8 families it belongs to, and the app tracks your score.

### Privacy
This app is entirely session-based. There are no accounts, no databases, and no persistent storage. Quiz state (score, stats) lives in your browser's session cookie and disappears when you close the tab. Nothing is tracked or logged.

## Families
At launch time the server loads all available families and their inaturalist taxa_id from the src/families.toml file. By default this file only contains the eight tutorial families and they are enabled by default. The user can choose from among the enabled families to set the scope of the quiz during their session.

### Default to Tutorial Families
- **Asteraceae** — Aster / Sunflower
- **Apiaceae** — Parsley / Carrot
- **Brassicaceae** — Mustard
- **Fabaceae** — Pea
- **Lamiaceae** — Mint
- **Liliaceae** — Lily
- **Poaceae** — Grass
- **Rosaceae** — Rose

### Others
The rest of the families in the book will be made available in the src/families.toml file. Uncomment them to enable them in the settings menu. Use the default variable to set whether they should be enabled by default.

Here is an example additonal family entry. These can be used for arbitrary families from iNaturalist.

```toml
[[family]]
name = "Lamiaceae"
common = "Mint Family"
taxon_id = 48623
default = true # Toggled on at app launch.
```

## How to Run
This app is intended to be selfhosted with docker. After launching the server, open http://localhost:5000.

### Selfhosting
#### Docker Run
```bash
docker pull dankleeman/botany-in-a-day
docker run -e SECRET_KEY=your-secret-here -p 5000:5000 dankleeman/botany-in-a-day
```

#### Docker Compose
It is recommended to use a .env from the .env.example.

```bash
cp .env.example .env
```

Then after setting your secret key in the .env file you can have your docker-compose.yml file point to that.

```yml
services:
  botany:
    image: dankleeman/botany-in-a-day-test:latest
    container_name: botany-in-a-day
    ports:
      - "5000:5000"
    env_file: .env
    restart: unless-stopped
```

### Running From Source
#### Flask Debug Mode
```bash
uv run 
```

#### Docker Compose
```bash
cp .env.example .env
# Edit .env and set a real SECRET_KEY
docker compose up --build
```

### Configuration

See `.env.example` for all available options:

- `SECRET_KEY` — required for session security
- `BATCH_SIZE` — number of observations to prefetch per family (default: 20)
- `PLACE_ID` — iNaturalist [place ID](https://www.inaturalist.org/places) to filter observations by region (default: `97394` = North America). Search for your region on iNaturalist and grab the numeric ID from the URL.
- `FLOWERING_ONLY` — only show flowering plant photos (default: `true`). Set to `false` to include fruiting, vegetative, and other observations.
- `THEME_BG`, `THEME_TEXT`, `THEME_ACCENT`, `THEME_ACCENT_HOVER` — optional color overrides

A light/dark theme toggle is available in the top-right corner of the app.

## Development

Requires [uv](https://docs.astral.sh/uv/) for local development.

```bash
# Install dependencies
uv sync

# Run the dev server
just dev

# Run all checks (lint, typecheck, tests)
just all

# Individual targets
just check       # ruff lint + format check
just typecheck   # ty check
just test        # pytest
just format      # auto-fix lint + formatting
```

## iNaturalist API Usage

This app uses the [iNaturalist API](https://api.inaturalist.org/v1/docs/) to fetch observation photos. iNaturalist asks that third-party apps stay under **100 requests/minute** (recommending ~60/min) and under **10,000 requests/day**. See their [API Recommended Practices](https://www.inaturalist.org/pages/api+recommended+practices) for details.

The app prefetches observations in batches (default 20 per family) so that answering questions doesn't require a request each time — only loading a new batch does. Normal quiz usage should stay well within iNaturalist's limits. If you're self-hosting for multiple users, consider increasing `BATCH_SIZE` to reduce request frequency.

## License
This project is licensed with the MIT license as detailed in the LICENSE file in this repository.
