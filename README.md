# Alkosto AI Assistant

AI Sales Assistant für Alkosto mit Streamlit Cloud Deployment.

## 🚀 Quick Deploy

### Schritt 1: GitHub
Repository: `https://github.com/Wunderbot-Git/alkosto-ai-assistant`

### Schritt 2: Streamlit Cloud
1. Gehe zu https://share.streamlit.io
2. Sign in mit GitHub
3. Click "New app"
4. Repository: `Wunderbot-Git/alkosto-ai-assistant`
5. Main file path: `streamlit_app.py`
6. Click "Deploy"

### Schritt 3: Secrets konfigurieren
1. In Streamlit Cloud → App → Settings → Secrets
2. Füge hinzu:
```toml
ALGOLIA_API_KEY = "a0e524e91a99723b11a1ea7bab1e504a"
```

### Schritt 4: Fertig!
Die App läuft unter: `https://alkosto-ai-assistant-XXXX.streamlit.app`

## 🎯 Features

- ✅ Konversationsbasierte Laptop-Beratung
- ✅ Algolia-Suche mit 317 Produkten
- ✅ Intelligente Filter (Budget, Gewicht, Akku)
- ✅ Produkt-Empfehlungen mit Begründungen
- ✅ Responsive Design für Desktop & Mobile
- ✅ Demo-Mode als Fallback

## 📁 Struktur

```
alkosto-ai-assistant/
├── streamlit_app.py          # Haupt-App
├── src/
│   └── algolia_client.py     # Algolia Client (Python)
├── requirements.txt          # Python Dependencies
└── .streamlit/
    └── secrets.toml          # Secrets Template
```

## 🔧 Lokale Entwicklung

```bash
pip install -r requirements.txt
export ALGOLIA_API_KEY="a0e524e91a99723b11a1ea7bab1e504a"
streamlit run streamlit_app.py
```

## 🧪 Tests

```bash
pytest test_algolia_client.py -v
```

## 📊 Algolia Index

- **App ID:** QX5IPS1B1Q
- **Index:** test_Philipp
- **Produkte:** 317 Laptops & Tablets

---

Erstellt für Philipp Hasskamp | AI Pro Kurs
