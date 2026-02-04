import json
import argparse
import urllib.parse
import random
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


# Pool di User-Agent realistici (browser recenti)
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
]


def get_random_user_agent() -> str:
    """Restituisce un User-Agent casuale dal pool."""
    return random.choice(USER_AGENTS)


def random_delay(min_seconds: float = 2.0, max_seconds: float = 8.0) -> None:
    """Applica un ritardo casuale per simulare comportamento umano."""
    delay = random.uniform(min_seconds, max_seconds)
    print(f"Attesa di {delay:.1f} secondi...")
    time.sleep(delay)


def simulate_human_behavior(page) -> None:
    """Simula comportamento umano con scroll e movimenti mouse casuali."""
    # Scroll casuale
    scroll_amount = random.randint(100, 400)
    page.mouse.wheel(0, scroll_amount)
    page.wait_for_timeout(random.randint(300, 800))

    # Torna su
    page.mouse.wheel(0, -scroll_amount // 2)
    page.wait_for_timeout(random.randint(200, 500))

    # Movimento mouse casuale
    for _ in range(random.randint(2, 4)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        page.mouse.move(x, y)
        page.wait_for_timeout(random.randint(50, 150))


def get_stealth_scripts() -> str:
    """Script JS per nascondere i segnali di automazione Playwright."""
    return """
    // Nascondi webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });

    // Nascondi automazione Chrome
    window.chrome = {
        runtime: {},
    };

    // Nascondi permessi
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );

    // Plugin realistici
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
            { name: 'Native Client', filename: 'internal-nacl-plugin' },
        ],
    });

    // Lingue realistiche
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en', 'it'],
    });

    // Hardware concurrency realistico
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
    });

    // Device memory realistico
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8,
    });

    // Nascondi automation flags
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    """


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
    min_delay: float = 2.0,
    max_delay: float = 8.0,
    start_from_homepage: bool = True,
) -> dict:
    """
    Query Google AI Mode using Playwright.

    Args:
        query: The search query
        headless: Run browser in headless mode (default: True)
        timeout: Timeout in milliseconds for AI response (default: 30000)
        locale: Browser locale (default: en-US)
        screenshot_path: Path to save screenshot for debugging (optional)
        min_delay: Minimum delay in seconds before request (default: 2.0)
        max_delay: Maximum delay in seconds before request (default: 8.0)
        start_from_homepage: Visit Google homepage first (default: True)

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
        "user_agent": None,
    }

    # Applica ritardo casuale prima della richiesta
    random_delay(min_delay, max_delay)

    # Seleziona User-Agent casuale
    user_agent = get_random_user_agent()
    result["user_agent"] = user_agent
    print(f"User-Agent: {user_agent[:50]}...")

    with sync_playwright() as p:
        # Args per sembrare un browser normale
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--disable-browser-side-navigation",
            "--disable-gpu",
            "--no-first-run",
            "--no-service-autorun",
            "--password-store=basic",
            "--use-mock-keychain",
        ]

        browser = p.chromium.launch(
            headless=headless,
            args=browser_args,
        )

        # Viewport casuali per sembrare più umani
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1280, "height": 720},
            {"width": 1440, "height": 900},
        ]
        viewport = random.choice(viewports)

        # Timezone casuali realistici
        timezones = [
            "Europe/Rome",
            "Europe/London",
            "America/New_York",
            "America/Los_Angeles",
        ]

        context = browser.new_context(
            locale=locale,
            user_agent=user_agent,
            viewport=viewport,
            timezone_id=random.choice(timezones),
            geolocation=None,
            permissions=[],
        )

        # Inietta script stealth prima di ogni pagina
        context.add_init_script(get_stealth_scripts())

        page = context.new_page()

        try:
            # Opzionalmente parti dalla homepage (più naturale)
            if start_from_homepage:
                print("Visitando prima la homepage di Google...")
                page.goto("https://www.google.com", wait_until="networkidle", timeout=timeout)
                page.wait_for_timeout(random.randint(1000, 2000))

                # Accetta cookie sulla homepage se necessario
                try:
                    accept_btn = page.locator(
                        "button:has-text('Accept all'), "
                        "button:has-text('Accept'), "
                        "button:has-text('Accetta tutto'), "
                        "button:has-text('Accetta')"
                    )
                    if accept_btn.count() > 0:
                        accept_btn.first.click(timeout=3000)
                        page.wait_for_timeout(random.randint(500, 1000))
                except PlaywrightTimeout:
                    pass

                # Simula digitazione nella search box
                search_box = page.locator("textarea[name='q'], input[name='q']").first
                if search_box.count() > 0:
                    search_box.click()
                    page.wait_for_timeout(random.randint(200, 500))

                    # Digita carattere per carattere (più umano)
                    for char in query:
                        search_box.type(char, delay=random.randint(50, 150))

                    page.wait_for_timeout(random.randint(300, 700))

                    # Cerca tramite submit invece che andando direttamente all'URL
                    page.keyboard.press("Enter")
                    page.wait_for_load_state("networkidle")

                    # Ora naviga alla versione AI Mode
                    page.wait_for_timeout(random.randint(500, 1000))

            # Vai all'URL AI Mode (o se partito dalla homepage, aggiungi udm=50)
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

            # Simula comportamento umano (scroll, mouse)
            simulate_human_behavior(page)

            # Wait a bit for AI content to load (it can be async)
            page.wait_for_timeout(random.randint(1500, 3000))

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
    parser.add_argument(
        "--min-delay",
        type=float,
        default=2.0,
        help="Ritardo minimo in secondi prima della richiesta (default: 2.0)",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=8.0,
        help="Ritardo massimo in secondi prima della richiesta (default: 8.0)",
    )
    parser.add_argument(
        "--no-delay",
        action="store_true",
        help="Disabilita il ritardo (utile per test)",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Vai direttamente all'URL (salta la homepage)",
    )

    args = parser.parse_args()

    print(f"Cercando: {args.query}")
    print("Attendere...")

    # Configura ritardi
    min_delay = 0.0 if args.no_delay else args.min_delay
    max_delay = 0.0 if args.no_delay else args.max_delay

    result = query_google_ai_mode(
        query=args.query,
        headless=not args.no_headless,
        timeout=args.timeout,
        locale=args.locale,
        screenshot_path=args.screenshot,
        min_delay=min_delay,
        max_delay=max_delay,
        start_from_homepage=not args.direct,
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
