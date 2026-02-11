# 🚀 Streamlit Cloud Deployment Guide

## Schritt 1: GitHub Repo erstellen

1. Gehe zu github.com
2. Erstelle neues Repo: `alkosto-ai-assistant`
3. Lade diese Dateien hoch:
   - `app.py` (die Streamlit App)
   - `requirements.txt`
   - `.gitignore`

## Schritt 2: Dateien vorbereiten

### requirements.txt
```
streamlit>=1.28.0
```

### .gitignore
```
__pycache__/
*.pyc
.DS_Store
.env
```

## Schritt 3: Deploy auf Streamlit Cloud

1. Gehe zu [share.streamlit.io](https://share.streamlit.io)
2. Sign in mit GitHub
3. Click "New app"
4. Wähle dein Repo: `alkosto-ai-assistant`
5. Main file path: `app.py`
6. Click "Deploy"

**Fertig!** Die App läuft in 2 Minuten und ist weltweit erreichbar.

## Schritt 4: Algolia API Key als Secret

1. In Streamlit Cloud → App → Settings → Secrets
2. Füge hinzu:
```toml
ALGOLIA_API_KEY = "your_key_here"
```

## Alternative: Sofortiger Zugriff (ohne Cloud)

### Option A: SSH Tunnel (sicher)
```bash
# Auf deinem Mac
ssh -L 8501:localhost:8501 root@76.13.113.207

# Dann im Browser (auch auf Handy via Port-Forwarding App)
http://localhost:8501
```

### Option B: Ngrok (temporärer öffentlicher Link)
```bash
# Auf dem Server installieren
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Authentifizieren (kostenloser Account auf ngrok.com)
ngrok config add-authtoken DEIN_TOKEN

# Tunnel starten
ngrok http 8501

# Öffentliche URL wird angezeigt (z.B. https://abc123.ngrok.io)
# Diese URL kannst du auf dem Handy öffnen!
```

## Handy-Zugriff

Sobald deployed:
1. Öffne die URL im Handy-Browser
2. Füge zu Homescreen hinzu (funktioniert wie native App)
3. Chat-Interface ist touch-optimiert

**Vorteile Streamlit Cloud:**
- ✅ Kostenlos
- ✅ Immer erreichbar
- ✅ Automatische HTTPS
- ✅ Kein Server-Management
- ✅ Echtzeit-Updates bei Git-Push

