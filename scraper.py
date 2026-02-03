import json
import os
import requests
from typing import Optional


def query_google_ai_mode(
    query: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    geo_location: str = "Italy",
    render: str = "html",
    parse: bool = True,
) -> dict:
    """
    Query Google AI Mode via Oxylabs API.

    Args:
        query: The search query
        username: Oxylabs username (or set OXYLABS_USERNAME env var)
        password: Oxylabs password (or set OXYLABS_PASSWORD env var)
        geo_location: Geographic location for the search
        render: Render mode ('html' recommended)
        parse: Whether to parse the response

    Returns:
        Parsed JSON response from Google AI Mode
    """
    username = username or os.getenv("OXYLABS_USERNAME")
    password = password or os.getenv("OXYLABS_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Credenziali mancanti. Imposta OXYLABS_USERNAME e OXYLABS_PASSWORD "
            "come variabili d'ambiente o passale come parametri."
        )

    payload = {
        "source": "google_ai_mode",
        "query": query,
        "render": render,
        "parse": parse,
        "geo_location": geo_location,
    }

    response = requests.post(
        "https://realtime.oxylabs.io/v1/queries",
        auth=(username, password),
        json=payload,
        timeout=60,
    )

    response.raise_for_status()
    return response.json()


def save_response(data: dict, filename: str = "response.json") -> None:
    """Save response to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Risposta salvata in: {filename}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Query Google AI Mode via Oxylabs")
    parser.add_argument("query", help="La query da cercare")
    parser.add_argument("--geo", default="Italy", help="Geolocalizzazione (default: Italy)")
    parser.add_argument("--output", "-o", default="response.json", help="File di output")

    args = parser.parse_args()

    try:
        result = query_google_ai_mode(query=args.query, geo_location=args.geo)
        save_response(result, args.output)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP: {e}")
    except ValueError as e:
        print(f"Errore: {e}")
