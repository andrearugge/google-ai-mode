# Google AI Mode Scraper

Script Python per interrogare Google AI Mode e ottenere risposte in formato JSON, senza necessità di API key o servizi a pagamento.

Utilizza [Playwright](https://playwright.dev/) per simulare un browser e navigare alla pagina di ricerca Google con AI Mode attivo.

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

### Esempi

```bash
# Query semplice
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
  "error": null
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

## Verifica AI Mode

Lo script verifica automaticamente se la risposta proviene effettivamente da Google AI Mode controllando:

1. **URL**: presenza del parametro `udm=50`
2. **DOM**: presenza di elementi specifici di AI Mode (`[data-ai-overview]`, `.AIOverview`, ecc.)

Se `ai_mode_verified` è `false`, significa che Google potrebbe aver rediretto alla ricerca normale. Usa `--screenshot` per verificare visivamente cosa è successo.

## Utilizzo come modulo Python

```python
from scraper import query_google_ai_mode

result = query_google_ai_mode(
    query="la tua query",
    headless=True,
    timeout=30000,
    locale="it-IT",
    screenshot_path="debug.png"
)

if result["ai_mode_verified"]:
    print(result["ai_response"])
else:
    print("AI Mode non disponibile")
```

## Limitazioni

- **Rate limiting**: Google potrebbe bloccare richieste troppo frequenti
- **CAPTCHA**: In caso di troppe richieste, potrebbe apparire un CAPTCHA
- **Disponibilità**: Google AI Mode potrebbe non essere disponibile in tutte le regioni
- **Selettori CSS**: I selettori potrebbero cambiare se Google aggiorna l'interfaccia
- **Terms of Service**: Lo scraping potrebbe violare i ToS di Google

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

## License

MIT
