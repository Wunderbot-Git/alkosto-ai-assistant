# 🤖 Alkosto AI Sales Assistant

AI-gestützter Verkaufsassistent für Alkosto (kolumbianischer Elektronik-Händler).
Berät Kunden bei der Laptop-Auswahl aus einem Katalog von 317 Produkten.

## 🚀 Quick Start

### Option 1: CLI (Node.js)
```bash
cd /home/alkosto-assistant
npm install
node src/cli.js
```

### Option 2: Streamlit UI (Python)
```bash
cd /home/alkosto-assistant
pip install streamlit
streamlit run src/app.py
```

### Option 3: Query Test
```bash
node src/test-query.js
```

## 📁 Struktur

```
alkosto-assistant/
├── src/
│   ├── cli.js              # CLI Prototyp
│   ├── test-query.js       # Query Generator Test
│   ├── app.py              # Streamlit UI
│   ├── algoliaClient.js    # Algolia API Client
│   └── prompts/
│       └── systemPrompt.js # System Prompt für Claude
├── data/                   # Lokale Daten
├── tests/                  # Tests
└── docs/                   # Dokumentation
```

## 🔧 Konfiguration

Für echte Algolia-Daten, erstelle `.env`:
```
ALGOLIA_API_KEY=your_search_api_key
```

Ohne API Key läuft der Assistant im Demo-Modus mit Beispiel-Daten.

## 🎯 Features

- ✅ Bedarfsanalyse (Use Case, Budget, Prioritäten)
- ✅ Automatische Algolia-Query-Generierung
- ✅ Produkt-Empfehlungen mit Begründungen
- ✅ Guardrails (Budget-Check, Verfügbarkeit)
- 🔄 Streamlit Chat-Interface
- ⏳ Echte Algolia-Integration (wenn API Key)

