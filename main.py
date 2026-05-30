import sys
from datetime import datetime
from pathlib import Path

import db
import matcher
import scraper

MATCHES_PATH = Path(__file__).parent / "matches.md"


def main():
    print(f"=== Rental Monitor — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC ===\n")

    db.init()

    # Reset new-flags before scraping so only today's arrivals are flagged
    db.mark_all_not_new()

    print("--- Scraping hybel.no ---")
    listings = scraper.scrape_all()

    print("\n--- Updating database ---")
    new_count = sum(1 for l in listings if db.upsert(l))

    stats = db.stats()
    print(f"Total in DB: {stats['total']}  |  New today: {stats['new']}")

    print("\n--- Running AI matcher ---")
    all_listings = db.get_all()
    match_output, has_new_matches = matcher.run(all_listings)

    header = (
        f"# Rental Matches — Trondheim\n\n"
        f"_Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC_  \n"
        f"_Database: {stats['total']} total listings | {stats['new']} new today_\n\n"
        f"---\n\n"
    )
    MATCHES_PATH.write_text(header + match_output + "\n")
    print("Wrote matches.md")

    if has_new_matches:
        print(f"\nNew matching listings found — signalling for notification.")
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
