from __future__ import annotations

import json
import os
import sys
from typing import Any

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0

UNRAVEL_URLS = [
    "https://unravel.tech",
    "https://unravel.tech/blog",
    "https://unravel.tech/talks",
]


def scrape_unravel_profiles() -> str:
    """
    Scrape unravel.tech pages to gather text content about founders and team.
    Returns the combined text from all pages for the LLM to analyze.
    """
    all_text = []

    for url in UNRAVEL_URLS:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove script and style tags
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            all_text.append(f"--- Content from {url} ---\n{text}")
        except requests.RequestException as exc:
            print(f"Warning: Could not fetch {url}: {exc}", file=sys.stderr)

    if not all_text:
        print("Error: Could not fetch any content from unravel.tech", file=sys.stderr)
        sys.exit(1)

    return "\n\n".join(all_text)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SEARCH_SUBSTRING = "pr"

SYSTEM_PROMPT = f"""You are a precise data-extraction agent.

You will receive scraped web content from unravel.tech (a senior engineering consulting company).

Follow these steps IN ORDER:

Step 1: List ALL founders/co-founders of Unravel.tech you can find in the content.

Step 2: For EACH founder, check if their **first name** (not last name) contains
the exact substring "{SEARCH_SUBSTRING}" (case-insensitive).
For example: "Prajwalit" contains "pr", but "Vedang" does NOT contain "pr".

Step 3: For the matching founder, construct their email:
   firstname@unrel.tech  (all lowercase, no spaces or separators).

Step 4: Return ONLY a JSON object with exactly two keys:
   - "founder_name": the matching founder's full name
   - "email": the constructed email

If no founder's first name contains "{SEARCH_SUBSTRING}", return:
  {{"founder_name": null, "email": null}}

IMPORTANT: Return ONLY the raw JSON. No markdown, no explanation.
"""


def build_user_prompt(profiles: str) -> str:
    """Construct the user message that carries the scraped content."""
    return f"Scraped content from unravel.tech:\n\n{profiles}"


def extract_founder_info(profiles: str) -> dict[str, Any]:
    """
    Call the LLM to extract founder information from scraped web content.
    """

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print(
            "Error: GROQ_API_KEY environment variable is not set.\n"
            "Get a free key at: https://console.groq.com/keys\n"
            "Then add to your .env file:  GROQ_API_KEY=gsk_...",
            file=sys.stderr,
        )
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(profiles)},
            ],
            temperature=TEMPERATURE,
            response_format={"type": "json_object"},
        )
    except OpenAIError as exc:
        print(f"Groq API error: {exc}", file=sys.stderr)
        sys.exit(1)

    raw_content = response.choices[0].message.content
    if not raw_content:
        print("Error: LLM returned an empty response.", file=sys.stderr)
        sys.exit(1)

    try:
        result = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        print(
            f"Error: Failed to parse LLM response as JSON.\n"
            f"Raw response: {raw_content}\n"
            f"Parse error:  {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    return result

def main() -> None:
    """Run the agent: scrape unravel.tech → extract founder info via LLM."""

    print("🌐 Scraping unravel.tech for founder profiles...")
    profiles = scrape_unravel_profiles()
    print(f"   Fetched {len(profiles)} characters of content.\n")

    print("🤖 Analyzing with LLM agent...")
    result = extract_founder_info(profiles)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()