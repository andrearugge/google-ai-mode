import json
import argparse
import urllib.parse
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


# Selectors that are SPECIFIC to Google AI Mode
# These help verify we're actually getting AI-generated content
AI_MODE_INDICATORS = [
    # AI Mode specific elements
    "[data-ai-overview]",
    "[data-attrid='AIOverview']",
    ".AIOverview",
    # AI Mode tab/button that should be active
    "[data-udm='50']",
    # Common AI response containers
    "[jsname='N760b']",
    "[data-hveid][data-ved] .wDYxhc",
]

# Selectors for extracting AI content once we've confirmed AI Mode
AI_CONTENT_SELECTORS = [
    "[data-ai-overview]",
    ".AIOverview",
    "[jsname='N760b']",
    ".wDYxhc[data-hveid]",
    "#center_col .wDYxhc",
]


def verify_ai_mode(page) -> dict:
    """
    Verify that we're actually in Google AI Mode.
    Returns verification details.
    """
    verification = {
        "is_ai_mode": False,
        "url_has_udm50": False,
        "ai_elements_found": [],
        "page_title": "",
        "final_url": "",
    }

    # Check URL
    current_url = page.url
    verification["final_url"] = current_url
    verification["url_has_udm50"] = "udm=50" in current_url

    # Check page title
    verification["page_title"] = page.title()

    # Look for AI Mode specific elements
    for selector in AI_MODE_INDICATORS:
        try:
            if page.locator(selector).count() > 0:
                verification["ai_elements_found"].append(selector)
        except Exception:
            pass

    # Determine if we're in AI Mode
    verification["is_ai_mode"] = (
        verification["url_has_udm50"] and len(verification["ai_elements_found"]) > 0
    )

    return verification


def query_google_ai_mode(
    query: str,
    headless: bool = True,
    timeout: int = 30000,
    locale: str = "en-US",
    screenshot_path: str = None,
) -> dict:
    """
    Query Google AI Mode using Playwright.

    Args:
        query: The search query
        headless: Run browser in headless mode (default: True)
        timeout: Timeout in milliseconds for AI response (default: 30000)
        locale: Browser locale (default: en-US)
        screenshot_path: Path to save screenshot for debugging (optional)

    Returns:
        Dict with query, AI response, sources, verification info, and metadata
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded_query}&udm=50"

    result = {
        "query": query,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "ai_mode_verified": False,
        "verification_details": {},
        "ai_response": None,
        "sources": [],
        "screenshot": None,
        "error": None,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            locale=locale,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=timeout)

            # Accept cookies if dialog appears
            try:
                accept_btn = page.locator(
                    "button:has-text('Accept all'), "
                    "button:has-text('Accept'), "
                    "button:has-text('Accetta tutto'), "
                    "button:has-text('Accetta')"
                )
                if accept_btn.count() > 0:
                    accept_btn.first.click(timeout=3000)
                    page.wait_for_timeout(1000)  # Wait for dialog to close
            except PlaywrightTimeout:
                pass

            # Wait a bit for AI content to load (it can be async)
            page.wait_for_timeout(2000)

            # Verify we're in AI Mode
            verification = verify_ai_mode(page)
            result["verification_details"] = verification
            result["ai_mode_verified"] = verification["is_ai_mode"]

            # Take screenshot if requested
            if screenshot_path:
                page.screenshot(path=screenshot_path, full_page=True)
                result["screenshot"] = screenshot_path
                print(f"Screenshot salvato: {screenshot_path}")

            # If not in AI Mode, warn but still try to get content
            if not verification["is_ai_mode"]:
                result["error"] = (
                    "AI Mode non verificato. "
                    f"URL contiene udm=50: {verification['url_has_udm50']}, "
                    f"Elementi AI trovati: {len(verification['ai_elements_found'])}. "
                    "Google potrebbe aver rediretto alla ricerca normale."
                )

            # Try to extract AI content
            ai_content = None
            matched_selector = None

            for selector in AI_CONTENT_SELECTORS:
                try:
                    element = page.locator(selector).first
                    if element.count() > 0:
                        content = element.text_content()
                        if content and len(content.strip()) > 50:  # Ensure meaningful content
                            ai_content = content.strip()
                            matched_selector = selector
                            break
                except Exception:
                    continue

            if ai_content:
                result["ai_response"] = ai_content
                result["matched_selector"] = matched_selector
            else:
                if not result["error"]:
                    result["error"] = "Nessun contenuto AI trovato"

            # Extract source links
            try:
                links = page.locator("a[href^='http']").all()
                seen_urls = set()
                for link in links[:20]:
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
            result["error"] = f"Timeout dopo {timeout}ms"
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
        help="Timeout in ms (default: 30000)",
    )
    parser.add_argument(
        "--locale",
        default="en-US",
        help="Locale del browser (default: en-US)",
    )
    parser.add_argument(
        "--output", "-o",
        default="response.json",
        help="File di output JSON (default: response.json)",
    )
    parser.add_argument(
        "--screenshot", "-s",
        help="Salva screenshot della pagina (es: screenshot.png)",
    )

    args = parser.parse_args()

    print(f"Cercando: {args.query}")
    print("Attendere...")

    result = query_google_ai_mode(
        query=args.query,
        headless=not args.no_headless,
        timeout=args.timeout,
        locale=args.locale,
        screenshot_path=args.screenshot,
    )

    save_response(result, args.output)

    # Print verification status
    print("\n--- Verifica AI Mode ---")
    v = result["verification_details"]
    print(f"URL contiene udm=50: {'Si' if v.get('url_has_udm50') else 'No'}")
    print(f"Elementi AI trovati: {len(v.get('ai_elements_found', []))}")
    print(f"AI Mode verificato: {'SI' if result['ai_mode_verified'] else 'NO'}")

    if result["error"]:
        print(f"\nAttenzione: {result['error']}")

    if result["ai_response"]:
        response_preview = result["ai_response"][:500]
        print(f"\n--- Risposta AI ---\n{response_preview}{'...' if len(result['ai_response']) > 500 else ''}")
        print(f"\nFonti trovate: {len(result['sources'])}")
    else:
        print("\nNessuna risposta AI trovata.")
