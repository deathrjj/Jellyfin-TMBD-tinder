#!/usr/bin/env python3
import os
import sys
import time
import csv
import requests

# ─── CONFIG ────────────────────────────────────────────────────────────────────
# Set your TMDb API key as an environment variable, e.g.:
#   export TMDB_API_KEY="your_key_here"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    print("ERROR: Please set TMDB_API_KEY in your environment.", file=sys.stderr)
    sys.exit(1)

INPUT_CSV = "Jellyfin.csv"
OUTPUT_CSV = "suggestions.csv"

# Rate-limit throttle (in seconds) between TMDb calls to avoid hitting request quotas
RATE_LIMIT = 0.25
# ────────────────────────────────────────────────────────────────────────────────


def tmdb_search(title: str, content_type: str) -> int:
    """
    Search TMDb for a movie or TV show by title.
    Returns the TMDb ID of the top result, or None if not found.
    """
    base_url = "https://api.themoviedb.org/3/search/"
    if content_type.lower() == "movie":
        url = base_url + "movie"
    elif content_type.lower() in ("show", "tv"):
        url = base_url + "tv"
    else:
        return None

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US",
        "page": 1,
        "include_adult": False,
    }

    resp = requests.get(url, params=params)
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return None
    return results[0].get("id")


def tmdb_get_similar(tmdb_id: int, content_type: str) -> list:
    """
    Given a TMDb ID and type ("movie" or "tv"), return a list of similar items.
    Each item is a dict with at least "title" (or "name") and "media_type".
    """
    if content_type.lower() == "movie":
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/similar"
    else:
        url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/similar"

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "page": 1,
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    return data.get("results", [])


def main():
    # 1) Read input CSV and build a set of already-downloaded names
    downloaded = set()
    entries = []
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Name"].strip()
            t = row["Type"].strip()
            downloaded.add(name.lower())
            entries.append((name, t))

    # 2) For each item in the input, search TMDb and fetch similar items
    suggestions_counter = {}
    for title, ctype in entries:
        tmdb_id = tmdb_search(title, ctype)
        time.sleep(RATE_LIMIT)
        if not tmdb_id:
            # No match found in TMDb; skip
            continue

        sim_list = tmdb_get_similar(tmdb_id, ctype)
        time.sleep(RATE_LIMIT)

        for sim in sim_list:
            # TMDb returns "title" for movies, "name" for TV
            sim_name = sim.get("title") or sim.get("name")
            if not sim_name:
                continue

            # Skip if already in our downloaded set
            if sim_name.lower() in downloaded:
                continue

            # Count frequency
            key = sim_name.strip()
            # Record type (movie/tv) based on what we fetched
            key_type = "Movie" if sim.get("media_type", ctype.lower()) == "movie" else "Show"
            # Use (name, type) as compound key so we know what type each suggestion is
            compound = (key, key_type)
            suggestions_counter[compound] = suggestions_counter.get(compound, 0) + 1

    # 3) Write out suggestions.csv sorted by count descending
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(["Name", "Type", "Count", "Shown"])
        # Sort by count descending
        for (name, t), count in sorted(suggestions_counter.items(), key=lambda kv: kv[1], reverse=True):
            writer.writerow([name, t, count, 0])

    print(f"Done. Suggestions written to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

