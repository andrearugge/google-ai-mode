import json
import argparse
import urllib.parse
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def query_google_ai_mode(
    query: str,
    headless: bool = True,
    timeout: int = 30000,
    locale: str = "en-US",
) -> dict:
    """
    Query Google AI Mode using Playwright.

    Args:
        query: The search query
        headless: Run browser in headless mode (default: True)
        timeout: Timeout in milliseconds for AI response (default: 30000)
        locale: Browser locale (default: en-US)

    Returns:
        Dict with query, AI response, sources, and metadata
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded_query}&udm=50"

    result = {
        "query": query,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "ai_response": None,
        "sources": [],
        "error": None,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            locale=locale,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded")

            # Accept cookies if dialog appears
            try:
                accept_btn = page.locator("button:has-text('Accept'), button:has-text('Accetta')")
                if accept_btn.count() > 0:
                    accept_btn.first.click(timeout=3000)
            except PlaywrightTimeout:
                pass

            # Wait for AI Mode content to load
            # Google AI Mode uses various selectors, we try multiple
            ai_selectors = [
                "[data-ai-overview]",
                ".AIOverview",
                "[jsname='N760b']",
                ".wDYxhc",  # Common container for AI responses
                "[data-attrid='AIOverview']",
            ]

            ai_content = None
            for selector in ai_selectors:
                try:
                    element = page.wait_for_selector(selector, timeout=timeout)
                    if element:
                        ai_content = element.text_content()
                        break
                except PlaywrightTimeout:
                    continue

            if ai_content:
                result["ai_response"] = ai_content.strip()
            else:
                # Fallback: try to get main content area
                try:
                    main_content = page.locator("#center_col").text_content()
                    result["ai_response"] = main_content.strip() if main_content else None
                except Exception:
                    result["error"] = "Could not find AI Mode response"

            # Extract source links
            try:
                links = page.locator("a[href^='http']").all()
                seen_urls = set()
                for link in links[:20]:  # Limit to first 20 links
                    href = link.get_attribute("href")
                    text = link.text_content()
                    if href and "google.com" not in href and href not in seen_urls:
                        seen_urls.add(href)
                        result["sources"].append({
                            "title": text.strip() if text else "",
                            "url": href,
                        })
            except Exception:
                pass

        except PlaywrightTimeout:
            result["error"] = f"Timeout after {timeout}ms waiting for AI response"
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()

    return result


def save_response(data: dict, filename: str = "response.json") -> None:
    """Save response to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Risposta salvata in: {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query Google AI Mode using Playwright (no API key required)"
    )
    parser.add_argument("query", help="La query da cercare")
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Mostra il browser (utile per debug)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Timeout in ms per la risposta AI (default: 30000)",
    )
    parser.add_argument(
        "--locale",
        default="en-US",
        help="Locale del browser (default: en-US)",
    )
    parser.add_argument(
        "--output", "-o",
        default="response.json",
        help="File di output (default: response.json)",
    )

    args = parser.parse_args()

    print(f"Cercando: {args.query}")
    print("Attendere...")

    result = query_google_ai_mode(
        query=args.query,
        headless=not args.no_headless,
        timeout=args.timeout,
        locale=args.locale,
    )

    save_response(result, args.output)

    if result["error"]:
        print(f"Errore: {result['error']}")
    else:
        print(f"\n--- Risposta AI ---\n{result['ai_response'][:500]}..." if result["ai_response"] and len(result["ai_response"]) > 500 else f"\n--- Risposta AI ---\n{result['ai_response']}")
        print(f"\nFonti trovate: {len(result['sources'])}")
