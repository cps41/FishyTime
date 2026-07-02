# FishyTime

Aggregates free public data sources (USGS streamflow, NWS weather, local moon/sun) to rank
Colorado Front Range trout waters by how good conditions look for fishing. Also a learning
project for building agentic LLM systems — see [REQUIREMENTS.md](REQUIREMENTS.md) for the
full requirements, verified data source notes, and the staged build plan.

**Status:** Stage 1 complete — a deterministic, no-LLM pipeline (data fetchers + a rules-based
scoring engine) with a CLI. No email delivery, no agent/LLM layer yet.

## Running it

The project targets Python 3.12 and is built to run inside its devcontainer so the environment
is reproducible:

```
docker build -f .devcontainer/Dockerfile -t fishytime-dev .
docker run --rm fishytime-dev fishytime               # today's report
docker run --rm fishytime-dev fishytime --date 2026-07-04
docker run --rm fishytime-dev pytest -v                # unit tests (mocked HTTP, no network)
```

Or open the folder in VS Code and "Reopen in Container" using `.devcontainer/devcontainer.json`.

`fishytime` prints a ranked report of the 5 configured waters for the target date, with the
reasoning behind each score and any caveats (missing gauge data, degraded sources, etc.).

## Layout

```
src/fishytime/
    config.py           WaterBody definitions (name, USGS gauge ID, coordinates)
    models.py            Shared dataclasses (StreamflowReading, WeatherReading, MoonInfo, ScoreResult, ...)
    timezones.py         Local display timezone (backend stores everything in UTC)
    data_sources/
        usgs.py           USGS Water Data API (streamflow, gage height, water temp)
        weather.py        NWS api.weather.gov (forecast, sky cover, pressure trend)
        moon.py           Local moon phase / sunrise-sunset (astral, no network call)
        stocking.py       Stub -- CPW stocking report, deferred (HTML-only, no API)
        snowpack.py       Stub -- SNOTEL snowpack, deferred
    scoring.py            score_conditions(): pure, deterministic, explainable weighted scoring
    pipeline.py           run_pipeline(): orchestrates fetchers + scoring per water body
    cli.py                fishytime command entry point
tests/                    pytest + responses (mocked HTTP), fixtures under tests/fixtures/
```

Every fetcher degrades to `None` on failure rather than raising -- a missing or broken data
source shows up as a caveat in the report instead of crashing the run.

## Roadmap

See the build stages in [REQUIREMENTS.md](REQUIREMENTS.md#build-stages-also-the-learning-path).
Next up: Stage 2, wrapping these fetchers as tools for a single-turn tool-calling agent.
