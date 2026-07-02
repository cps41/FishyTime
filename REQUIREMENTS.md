# FishyTime — Requirements

## Vision

A tool that tells you **when and where to fish** the Colorado Front Range, by pulling
free public data sources and turning them into a ranked, explained recommendation
delivered by email.

## Learning goals (equal priority to the fishing goal)

This project exists to build real, hands-on understanding of agentic LLM systems:

- Tool-calling / function-calling loops (LLM decides which tools to invoke, in what order)
- Structuring an agent around a **deterministic core** it can trust (scoring logic) vs.
  where LLM judgment actually adds value (synthesis, explanation, handling ambiguity)
- Handling messy/semi-structured real-world data (HTML scraping, missing gauges, stale reports)
  inside a tool an agent calls
- Observability basics: logging tool calls, token/cost tracking
- Running an LLM agent unattended on a schedule (not just interactively)

## V1 Scope

**In scope:**

- Region: Colorado Front Range
- Waters: South Platte (Cheesman Canyon / Deckers), Clear Creek, Boulder Creek,
  Chatfield Reservoir, Cherry Creek Reservoir
- Species: trout (rainbow/brown)
- Delivery: email digest
- Schedule: automated via GitHub Actions cron (e.g. Thursday evening, for the upcoming weekend)
  — chosen for V1 because it needs no cloud account and is fastest to get running; the
  scheduled-run logic should stay decoupled from GitHub Actions specifically so it can move
  to Azure Functions later (see Stage 7)

**Out of scope for V1** (candidate future work):

- Statewide coverage, warmwater species, other regions
- Web dashboard / map UI
- Conversational / on-demand chat interface
- Mobile push, SMS, Discord
- Backtesting recommendations against actual catch logs
- Azure Functions deployment (planned as the future runtime, see Stage 7)

## Data sources (all free, no paid keys required)

| Source | Provides | Access | Notes |
|---|---|---|---|
| USGS Water Data API | Streamflow, gage height, water temp | REST, no key (`api.waterdata.usgs.gov`; legacy `waterservices.usgs.gov` is migrating — use the new endpoint) | Per-gauge; need to map each water body to its gauge site ID |
| NWS/NOAA `api.weather.gov` | Forecast, temp, wind, precip, sky cover; barometric pressure trend | REST, no key, just needs a descriptive User-Agent header | Point forecast by lat/lon |
| NRCS SNOTEL (AWDB REST API) | Snowpack / snow-water-equivalent (runoff context, esp. spring) | REST, no key | Mostly relevant pre-runoff season |
| CPW Fish Stocking Report | Recently stocked waters (bonus signal) | **HTML table only** — no API/CSV. Fields: body of water, region, report date. Updated Fridays. | Needs a scraper; species/size aren't per-entry (report only covers catchable ~10" trout) |
| Moon phase, sunrise/sunset | Solunar timing signal | Computed locally (`astral` or similar) | No network call needed |

## Scoring logic (deterministic, not LLM)

A rules/weights engine scores each water body for the target window using:

- Water temp in trout-preferred range (~50–65°F)
- Flow stability / recent flow trend (spiking or dropping fast = bad)
- Barometric pressure trend (falling before a front, or stable = good; sharp high-pressure spike = bad)
- Wind, precip, cloud cover from forecast
- Recent stocking bonus (within ~1–2 weeks per CPW report)
- Time-of-day window (dawn/dusk preferred) and moon phase as a minor modifier

This logic must be plain code — testable and debuggable independent of the LLM.

## Where the LLM/agent fits

- Each data source is wrapped as a **tool** (`get_streamflow`, `get_weather_forecast`,
  `get_snowpack`, `get_stocking_report`, `get_moon_phase`, `score_conditions`).
- The agent decides which waters/gauges to check, calls the tools, calls `score_conditions`
  (deterministic), and then **synthesizes** the results into a ranked, plain-English
  recommendation with reasoning and caveats (e.g. "gauge offline, using nearby proxy").
- The LLM does not invent scores — it explains and ranks what the deterministic layer produced.

## Output (email digest) must include

- Ranked list of water bodies for the target window
- Short rationale per water body (why it ranks where it does)
- Best time-of-day window
- Confidence/caveats (stale or missing data, gauge outages)

## Non-functional requirements

- No paid API keys except the Anthropic API itself (usage should stay cheap — small number
  of scheduled runs per week, not continuous polling)
- Secrets (Anthropic API key, email credentials) via GitHub Actions secrets, never committed
- Missing/broken data source should degrade gracefully (skip + note in digest), never crash the run
- Stateless per run (no required persistent DB for V1)

## Build stages (also the learning path)

0. Repo scaffold, project structure, GitHub Actions skeleton
1. Deterministic pipeline: data fetchers + `score_conditions` as plain Python functions,
   unit-tested, runnable locally with no LLM involved — get something trustworthy first
2. Wrap fetchers as tools; single-turn tool-calling agent assembles and writes the digest
3. Multi-step agentic behavior: agent handles missing data, tries fallback gauges, decides
   which candidate waters are worth checking rather than a hardcoded list
4. Observability: log every tool call, tokens, and cost per run
5. (Stretch) On-demand chat mode over the latest digest/data
6. (Stretch) Fine-tune/distill a small local model on logged agent digests from Stage 4
   (structured scores → digest text), narrowly scoped to imitating the write-up style —
   not a replacement for the agent's reasoning, since there's no labeled ground truth
   for "good fishing day" to train a decision-maker on
7. (Future) Migrate the scheduled run from GitHub Actions to an Azure Function
   (timer trigger) — requires the run logic to already be a plain callable entry point
   (not GitHub-Actions-specific), an Azure subscription, and secrets moved to Azure
   Key Vault or Function App settings instead of GitHub Actions secrets

## Open questions to revisit later

- ~~Which specific USGS gauge IDs map to each water body~~ — resolved in Stage 1, see
  `src/fishytime/config.py`
- Exact CPW scraper resilience (site structure may change)
- Whether SNOTEL data is worth the complexity for V1 given Front Range trout focus in summer
- **USGS `api.waterdata.usgs.gov` enforces a rate limit** (`X-Ratelimit-Limit: 1000`, returns
  `429` with `Retry-After` once exhausted). Confirmed by hitting it during Stage 1 development.
  A scheduled run a few times a week (per the non-functional requirements) won't come close,
  but Stage 2+ should consider basic backoff/retry or at least distinguishing a 429 from "gauge
  has no data" in logs, since right now both degrade identically (silently to `None`).
