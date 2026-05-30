import os
from pathlib import Path
import anthropic

LOOKINGFOR_PATH = Path(__file__).parent / "lookingfor.md"
MODEL = "claude-haiku-4-5-20251001"


def load_criteria() -> str:
    if not LOOKINGFOR_PATH.exists():
        return ""
    return LOOKINGFOR_PATH.read_text().strip()


def _fmt(l: dict) -> str:
    rent = f"{l['rent']:,} kr/month".replace(",", " ") if l["rent"] else "Unknown"
    size = f"{l['size_sqm']}m²" if l["size_sqm"] else "Unknown"
    new_tag = " [NEW TODAY]" if l["is_new"] else ""
    return (
        f"ID:{l['id']}{new_tag}\n"
        f"Type: {l['housing_type'] or 'Unknown'}\n"
        f"Address: {l['address']}\n"
        f"Rent: {rent}\n"
        f"Size: {size}\n"
        f"URL: {l['url']}"
    )


def find_matches(listings: list[dict], criteria: str) -> str:
    if not criteria:
        return "_`lookingfor.md` is empty — add your search criteria to get matches._\n"

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    listings_text = "\n\n---\n\n".join(_fmt(l) for l in listings)

    prompt = f"""You are helping find rental listings that match a person's requirements in Trondheim, Norway.

## What they are looking for:
{criteria}

## Available listings ({len(listings)} total):
{listings_text}

## Instructions:
- Review every listing against the requirements
- Return ONLY listings that are a reasonable match
- Mark listings tagged [NEW TODAY] with 🆕
- Sort from best to worst fit
- Be concise — one sentence per match explaining why it fits
- If nothing matches, say so clearly

## Output format (markdown):

### [Address] — [Rent] kr/month
**Size:** Xm² | **Type:** [type] | 🆕 (if new)
**Why:** [one sentence]
[hybel.no link]

---

End with: `**X matching listings (Y new today)**`
"""

    msg = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def run(listings: list[dict]) -> tuple[str, bool]:
    """Returns (markdown_output, has_new_matches)."""
    criteria = load_criteria()
    output = find_matches(listings, criteria)
    has_new_matches = any(l["is_new"] for l in listings) and "🆕" in output
    return output, has_new_matches
