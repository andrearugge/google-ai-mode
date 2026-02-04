# Google AI Mode Scraper

Script Python per interrogare Google AI Mode e ottenere risposte in formato JSON, senza necessità di API key o servizi a pagamento.

Utilizza [Playwright](https://playwright.dev/) per simulare un browser e navigare alla pagina di ricerca Google con AI Mode attivo.

Include tecniche avanzate anti-detection per ridurre il rischio di essere bloccati da Google.

## Requisiti

- Python 3.8+
- Playwright

## Installazione

1. **Clona il repository:**
   ```bash
   git clone <url-del-repo>
   cd google-ai-mode
   ```

2. **Crea un virtual environment (consigliato):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oppure
   venv\Scripts\activate     # Windows
   ```

3. **Installa le dipendenze:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Installa il browser Chromium:**
   ```bash
   playwright install chromium
   ```

## Utilizzo

### Comando base

```bash
python scraper.py "la tua query"
```

### Opzioni disponibili

| Opzione | Descrizione | Default |
|---------|-------------|---------|
| `query` | La query da cercare (obbligatorio) | - |
| `--output`, `-o` | File di output JSON | `response.json` |
| `--screenshot`, `-s` | Salva screenshot della pagina | - |
| `--no-headless` | Mostra il browser (utile per debug) | `False` |
| `--timeout` | Timeout in millisecondi | `30000` |
| `--locale` | Locale del browser | `en-US` |
| `--min-delay` | Ritardo minimo in secondi prima della richiesta | `2.0` |
| `--max-delay` | Ritardo massimo in secondi prima della richiesta | `8.0` |
| `--no-delay` | Disabilita i ritardi (più veloce, meno sicuro) | `False` |
| `--direct` | Vai direttamente all'URL (salta la homepage) | `False` |

### Esempi

```bash
# Query semplice (con anti-detection attivo di default)
python scraper.py "best budget laptops 2024"

# Con screenshot per verificare visivamente
python scraper.py "migliori smartphone" --screenshot debug.png

# Vedere il browser in azione (debug)
python scraper.py "artificial intelligence" --no-headless

# Locale italiano
python scraper.py "intelligenza artificiale" --locale it-IT

# Output personalizzato con screenshot
python scraper.py "quantum computing" -o risultato.json -s pagina.png

# Timeout più lungo per connessioni lente
python scraper.py "machine learning" --timeout 60000

# Massima sicurezza anti-detection (ritardi più lunghi)
python scraper.py "AI news" --min-delay 5 --max-delay 15

# Modalità veloce (meno sicuro, più rapido)
python scraper.py "test query" --direct --no-delay

# Bilanciato: salta homepage ma mantieni ritardi
python scraper.py "python tutorial" --direct --min-delay 3 --max-delay 8
```

## Output

Lo script genera un file JSON con la seguente struttura:

```json
{
  "query": "best AI tools",
  "url": "https://www.google.com/search?q=best%20AI%20tools&udm=50",
  "timestamp": "2024-01-15T10:30:00.123456",
  "ai_mode_verified": true,
  "verification_details": {
    "is_ai_mode": true,
    "url_has_udm50": true,
    "ai_elements_found": ["[data-ai-overview]", "[data-udm='50']"],
    "final_url": "https://www.google.com/search?q=best%20AI%20tools&udm=50",
    "page_title": "best AI tools - Google Search"
  },
  "ai_response": "La risposta generata da Google AI Mode...",
  "sources": [
    {
      "title": "Titolo della fonte",
      "url": "https://esempio.com/articolo"
    }
  ],
  "screenshot": "debug.png",
  "error": null,
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
}
```

### Campi principali

| Campo | Descrizione |
|-------|-------------|
| `ai_mode_verified` | `true` se AI Mode è stato confermato |
| `verification_details` | Dettagli sulla verifica (URL, elementi trovati) |
| `ai_response` | Il testo della risposta generata da AI |
| `sources` | Lista delle fonti citate |
| `error` | Messaggio di errore (se presente) |
| `user_agent` | User-Agent utilizzato per la richiesta |

## Verifica AI Mode

Lo script verifica automaticamente se la risposta proviene effettivamente da Google AI Mode controllando:

1. **URL**: presenza del parametro `udm=50`
2. **DOM**: presenza di elementi specifici di AI Mode (`[data-ai-overview]`, `.AIOverview`, ecc.)

Se `ai_mode_verified` è `false`, significa che Google potrebbe aver rediretto alla ricerca normale. Usa `--screenshot` per verificare visivamente cosa è successo.

## Tecniche Anti-Detection

Lo script include diverse tecniche per evitare di essere rilevato come bot:

### 1. Rotazione User-Agent
Pool di 11 User-Agent realistici che vengono selezionati casualmente:
- Chrome (Windows/Mac)
- Firefox (Windows/Mac)
- Safari (Mac)
- Edge (Windows)

### 2. Ritardi Randomizzati
Pause casuali tra le richieste (configurabili con `--min-delay` e `--max-delay`) per simulare comportamento umano.

### 3. Navigazione da Homepage
Di default, lo script:
1. Visita prima `google.com`
2. Digita la query carattere per carattere (con delay casuali)
3. Preme Enter per cercare
4. Naviga alla versione AI Mode

Questo simula il comportamento di un utente reale. Usa `--direct` per saltare questo passaggio.

### 4. Simulazione Comportamento Umano
- Scroll casuale su/giù nella pagina
- Movimenti mouse randomizzati
- Tempi di attesa variabili

### 5. Stealth JavaScript
Script iniettati per nascondere i segnali di automazione:
- Nasconde `navigator.webdriver`
- Simula `chrome.runtime`
- Aggiunge plugin finti
- Imposta proprietà browser realistiche

### 6. Parametri Browser Casuali
- Viewport randomizzati (1920x1080, 1366x768, etc.)
- Timezone casuali (Europe/Rome, America/New_York, etc.)
- Flag Chrome per disabilitare segnali di automazione

## Utilizzo come modulo Python

```python
from scraper import query_google_ai_mode

result = query_google_ai_mode(
    query="la tua query",
    headless=True,
    timeout=30000,
    locale="it-IT",
    screenshot_path="debug.png",
    min_delay=2.0,
    max_delay=8.0,
    start_from_homepage=True,  # False per saltare la homepage
)

if result["ai_mode_verified"]:
    print(result["ai_response"])
else:
    print("AI Mode non disponibile")
```

## Limitazioni

- **Rate limiting**: Google potrebbe bloccare richieste troppo frequenti. Usa ritardi più lunghi (`--min-delay 10 --max-delay 20`) per richieste multiple
- **CAPTCHA**: In caso di troppe richieste, potrebbe apparire un CAPTCHA. Le tecniche anti-detection riducono questo rischio ma non lo eliminano
- **Disponibilità**: Google AI Mode potrebbe non essere disponibile in tutte le regioni
- **Selettori CSS**: I selettori potrebbero cambiare se Google aggiorna l'interfaccia
- **Terms of Service**: Lo scraping potrebbe violare i ToS di Google
- **VPN/Proxy**: Se usi VPN o proxy, potresti essere bloccato più facilmente

## Troubleshooting

### AI Mode non verificato
- Usa `--screenshot` per vedere cosa mostra Google
- Prova con `--no-headless` per debug interattivo
- Cambia locale con `--locale en-US`

### Timeout
- Aumenta il timeout con `--timeout 60000`
- Verifica la connessione internet

### Nessun contenuto trovato
- I selettori CSS potrebbero essere cambiati
- Google potrebbe aver modificato la struttura della pagina
- Verifica con screenshot e aggiorna i selettori in `AI_MODE_INDICATORS` e `AI_CONTENT_SELECTORS`

### Bloccato da Google / CAPTCHA
- Aumenta i ritardi: `--min-delay 10 --max-delay 20`
- Assicurati di non usare `--direct` (la navigazione da homepage è più naturale)
- Evita troppe richieste in poco tempo
- Prova a cambiare rete/IP
- Aspetta qualche ora prima di riprovare

## License

MIT
