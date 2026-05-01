# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2025-04-30

### Added
- RSS aggregation from 10 sources across Global, India, US, and Science categories
- AI summarisation via Ollama (local, free) and Groq (cloud free tier) — switchable via `AI_PROVIDER` env var
- Political bias detection with confidence score and reason per article
- Auto-categorisation into Tech, Science, Health, Sports, Politics, Business, Entertainment, Environment, General
- Tag extraction and estimated read time per article
- FastAPI backend with cursor-based pagination (immune to feed drift)
- APScheduler background jobs — RSS fetch every 30 min, summarise every 2 min
- React Native app for iOS and Android (Expo SDK 54)
- Article feed with infinite scroll and pull-to-refresh
- Article detail screen with AI summary box and bias analysis
- Category and region filter pills
- Light and dark theme — follows system default, user preference persisted via AsyncStorage
- MIT License

---

## [1.1.0] — 2025-04-30

### Changed
- Rebranded from Nuvera to **Verax** — name, logo, app icon, splash screen, all references
- Tagline updated to "The truth-teller."
- App icon — bold V lettermark with gold beam, navy background
- Splash screen — full Verax logo with wordmark
- Added Gemini AI provider support (`AI_PROVIDER=gemini`)
- Switched from offset-based to cursor-based pagination — eliminates duplicate articles on infinite scroll
- Dark theme now follows system default on first launch, persisted via AsyncStorage
- Bottom tab bar respects light/dark theme
- Category pill rows fixed — no longer clipped in horizontal ScrollView
- Deployed backend to Render + Supabase PostgreSQL
- Android APK published via Expo EAS Build

### Fixed
- Status bar overlap on all screens — switched to `SafeAreaView` from `react-native-safe-area-context`
- `connect_args` crash when switching from SQLite to PostgreSQL
- EAS build failing due to peer dependency conflicts — added `legacy-peer-deps` to `.npmrc`

---

## [1.4.0] — 2026-05-01

### Added
- Content-based recommendation engine (`recommender.py`) — TF-IDF vectorisation (scikit-learn, 10k features, bigrams, sublinear TF) scores every article against a user profile vector built from category preferences (0.50), positionally-decayed read history (0.30), and author affinity (0.20)
- Maximal Marginal Relevance (MMR) feed selection — replaces round-robin source interleaving; greedily picks articles that maximise relevance while penalising redundancy with already-selected articles, preventing the same story from multiple outlets flooding the feed
- Adaptive scoring weights — five signals (semantic similarity, recency, category affinity, region match, trending) with different weights for personalised vs cold-start mode; cold-start leans on trending (0.35) and recency (0.30) to surface breaking news for new users
- Soft category affinity matrix — adjacent categories (tech↔crypto 0.5, tech↔science 0.6, science↔health 0.5, etc.) receive partial scores instead of hard 0/1 binary, broadening relevant content
- Two-phase recency curve — flat 1.0 for the first 6 h (breaking news window), linear decay 6–48 h, exponential tail beyond 48 h with 36 h half-life; preserves quality day-old content
- Trending signal — cross-article cosine similarity identifies stories covered simultaneously by multiple sources; normalised fraction of recent articles on the same topic
- Read history tracking — `recordView(id, author)` on article open; IDs (max 50) and authors (max 30) stored in AsyncStorage; viewed articles excluded from feed output; used to build personalised user profile
- `author`, `rss_summary`, `source_tags` fields — captured from RSS feed metadata at scrape time; incorporated into TF-IDF corpus and user profile vector
- Expanded RSS sources from 70 to 135 — added Engadget, TechRadar, The Register, 9to5Mac, Android Authority, MIT AI News, Scientific American, Phys.org, Space.com, NHS UK, Harvard Health, CNBC, MarketWatch, The Economist, Carbon Brief, Grist, Bleacher Report, GameSpot, PC Gamer, The Block, Economic Times, Business Standard, India Today, Axios, The Hill, Vox, Sky News, Korea Herald, Jakarta Post, Dawn, and more across all regions and categories
- `scikit-learn==1.5.2`, `numpy==1.26.4`, `pandas==2.2.3` added to backend dependencies

### Changed
- `/news/recommended` endpoint — `filter_region` and `filter_category` hard SQL filters separate from soft `categories`/`regions` scoring preferences; `global` region pill treated as no-restriction (no SQL `WHERE region=` clause) rather than a tag filter
- Region + category SQL logic — specific region (e.g. `india`) + category sends only the category as a soft semantic preference to avoid near-zero SQL results (e.g. India has no tech-tagged sources); `global` + category applies the category as a hard SQL filter
- Regional pool broadening — regional filter includes global-tagged articles (`WHERE region IN (region, 'global')`) so thin regional categories (e.g. India + crypto) fall back to globally-relevant content; global articles scored at 0.3 region-match vs 1.0 for exact region
- Home feed routes all modes through `useRecommendedNews` — For You, category pills, and region pills all use the recommendation engine
- Pagination offset advances by actual returned page count (`lastPageParam + lastPage.length`) rather than total loaded, surviving recommender cache rebuilds mid-session

### Fixed
- All articles showing "Just now" — switched timestamp display from `created_at` (scrape insertion time) to `published_at` (actual RSS publish date); appended `Z` suffix to backend datetime strings so JavaScript parses them as UTC instead of local time
- Region pills showing identical content — `filter_region` hard SQL filter was missing; all regions were scoring identically
- India + crypto returning only 10 articles — regional filter now includes global articles in the candidate pool
- Summarizer writing multi-value categories (`tech|science|health`) — AI prompt rewritten to enforce single-word output; parsing sanitised with `split('|')[0]`
- Pagination stalling after first page — `getNextPageParam` now uses `lastPageParam + lastPage.length`; previous implementation using `allPages.flatMap().length` misaligned after cache rebuilds

---

## [Unreleased]

### Planned
- Multi-language support (Hindi, Tamil, Spanish, French, Arabic)
- Bookmarks — save articles offline
- Search across headlines and summaries
- Push notifications for breaking news
- User-defined RSS sources
- iOS App Store and Google Play release

---

## [1.3.0] — 2026-04-30

### Added
- 3-step onboarding flow — Welcome, region selection (11 regions), topic selection (11 categories); preferences saved to AsyncStorage; shown only on first launch
- Personalised feed — home feed defaults to "For You" using onboarding preferences; category and region pills override temporarily; preferred topics appear first in pill row
- `published_at` field on articles — RSS entry publish date captured at scrape time; feed sorted by actual publish date (`COALESCE(published_at, created_at) DESC`) instead of insertion order, naturally interleaving content across sources
- Compound pagination cursor `(before_ts, before_id)` — replaces single `before_id` cursor; eliminates skipped or duplicate articles when sorting by timestamp
- Multi-region and multi-category API filtering — `regions` and `categories` comma-separated query params with SQL `IN` filter; fully backward compatible with existing single-value params
- Expanded RSS sources to 70+ — added Australia (ABC, Guardian AU, SMH), Canada (CBC, Global News, Toronto Star), Europe (Euronews, POLITICO EU, DW), Middle East (Arab News, Jerusalem Post, Al Monitor), Africa (AllAfrica, Mail & Guardian, The East African), Latin America (Mercopress, Rio Times, Buenos Aires Herald), Asia Pacific (Japan Times, Straits Times, SCMP, Nikkei Asia), Entertainment (Variety, Hollywood Reporter, Rolling Stone, Pitchfork), Gaming (IGN, Polygon, Eurogamer), Crypto (CoinDesk, CoinTelegraph, Decrypt)
- `make kill-backend` target — `make run-backend` now kills port 8000 before starting, eliminates "Address already in use" error

### Fixed
- Splash screen flicker on launch — `SplashScreen.preventAutoHideAsync()` holds splash until onboarding check resolves; navigator mounts directly on the correct screen via `initialRouteName`, no redirect needed
- Feed double-query on launch — `FeedScreen` waits for preferences before mounting `Feed`; single correct query fires on first render, no wrong-then-right refetch
- Local dev API URL always `localhost` on physical device — `resolveBaseUrl()` derives host from `Constants.expoConfig.hostUri` (same IP as Metro bundler); `mobile/.env.local` was silently overriding `mobile/.env` due to Expo env priority
- `make run-backend` uses `venv/bin/uvicorn` — no longer requires global uvicorn install or manual venv activation

---

## [1.2.0] — 2026-04-30

### Added
- GitHub Actions CI workflow — runs on every PR to `main`, checks backend syntax and mobile TypeScript
- CODEOWNERS — all changes require approval from `@dhanasekaranweb`
- Branch protection on `main` — PRs required, force push blocked
- `Makefile` — `make check` runs full CI suite locally (mirrors GitHub Actions exactly); `make env-local/staging/production` switches environments without touching code; `make run-backend` and `make run-mobile HOST=<ip>` for local dev
- Multi-environment support — `APP_ENV=local|staging|production` selects the matching `.env.<env>` file; per-environment files for backend and mobile; `.env.example` committed as template
- Expanded RSS sources from 10 to 40+ covering Global, Tech, Science, Health, Business, Environment, Sports, India, US, UK

### Fixed
- `Skeleton` component `width` prop typed as `DimensionValue` instead of `string | number` — fixes TypeScript error in CI
- Infinite scroll double-trigger — `onEndReached` now uses a stable ref instead of recreating on every `isFetchingNextPage` change; threshold reduced from 0.4 to 0.2
- Local dev backend unreachable on physical device — `.env.local` now uses machine IP instead of `localhost`
- CI syntax check uses `python3` consistently across local and GitHub Actions
