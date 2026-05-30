# hybel.no rental monitor

Scrapes rental listings in Trondheim from hybel.no daily, stores them in a local SQLite database, and uses Claude AI to match them against your criteria in `lookingfor.md`. New matches trigger a GitHub Issue (which emails you).

## Setup

**1. Add your Anthropic API key**  
Repo → Settings → Secrets and variables → Actions → New secret  
Name: `ANTHROPIC_API_KEY`

**2. Edit `lookingfor.md`**  
Describe what you're looking for — budget, size, location, deal-breakers. Plain English is fine.

**3. Enable the workflow**  
Uncomment `.github/workflows/daily.yml` and push. The job runs daily at 09:00 Norway time.  
You can also trigger it manually from the Actions tab.

## How it works

1. Scrapes all pages of hybel.no/Trondheim (rooms, bedsits, shared housing)
2. Upserts listings into `data/listings.db` — new arrivals are flagged
3. Sends all listings + your `lookingfor.md` to Claude Haiku for matching
4. Writes results to `matches.md` and commits it back to the repo
5. If new listings match → opens a GitHub Issue so you get an email

## Files

| File | Purpose |
|------|---------|
| `lookingfor.md` | **Edit this** — your search criteria |
| `matches.md` | Auto-generated match report (do not edit) |
| `data/listings.db` | SQLite database of all seen listings |
| `scraper.py` | Fetches and parses hybel.no |
| `db.py` | Database read/write |
| `matcher.py` | Claude AI matching logic |
| `main.py` | Orchestrator |
