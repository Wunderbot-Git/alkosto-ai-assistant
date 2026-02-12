# Alkosto AI Assistant - Google Cloud Run Deployment

## Voraussetzungen

- Google Cloud Account (gcloud CLI installiert)
- Docker installiert (für lokale Tests)
- Dieses Repository geklont

## Schritt 1: Google Cloud Projekt einrichten

```bash
# Projekt erstellen (falls noch keines existiert)
gcloud projects create alkosto-ai-agent --name="Alkosto AI Assistant"

# Projekt auswählen
gcloud config set project alkosto-ai-agent

# Cloud Run API aktivieren
gcloud services enable run.googleapis.com
```

## Schritt 2: Docker Image bauen und pushen

```bash
# Google Container Registry konfigurieren
gcloud auth configure-docker

# Image bauen
docker build -t gcr.io/alkosto-ai-agent/alkosto-ai:latest .

# Image pushen
docker push gcr.io/alkosto-ai-agent/alkosto-ai:latest
```

## Schritt 3: Cloud Run Deployment

```bash
# Deploy mit Secrets als Umgebungsvariablen
gcloud run deploy alkosto-ai \
  --image gcr.io/alkosto-ai-agent/alkosto-ai:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=AIzaSyDipHWslKl1AFFc959vxk4yFRTsgVl4ROM \
  --set-env-vars ALGOLIA_API_KEY=a0e524e91a99723b11a1ea7bab1e504a \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

## Schritt 4: Secret Manager (sicherere Alternative)

Statt direkt in der CLI, verwende Google Secret Manager:

```bash
# Secrets erstellen
echo -n "AIzaSyDipHWslKl1AFFc959vxk4yFRTsgVl4ROM" | gcloud secrets create gemini-api-key --data-file=-
echo -n "a0e524e91a99723b11a1ea7bab1e504a" | gcloud secrets create algolia-api-key --data-file=-

# Deploy mit Secret Manager
gcloud run deploy alkosto-ai \
  --image gcr.io/alkosto-ai-agent/alkosto-ai:latest \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-secrets ALGOLIA_API_KEY=algolia-api-key:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Schritt 5: URL testen

Nach dem Deploy bekommst du eine URL:
```
https://alkosto-ai-XXXXXX-uc.a.run.app
```

Die App ist dann live!

## Updates deployen

```bash
# Änderungen commiten
git add .
git commit -m "Update"
git push origin main

# Neues Image bauen
docker build -t gcr.io/alkosto-ai-agent/alkosto-ai:latest .
docker push gcr.io/alkosto-ai-agent/alkosto-ai:latest

# Redeploy
gcloud run deploy alkosto-ai --image gcr.io/alkosto-ai-agent/alkosto-ai:latest
```

## Vorteile von Cloud Run

- ✅ Sichere Secret-Verwaltung
- ✅ Skaliert automatisch (0 → 1000 Instanzen)
- ✅ Pay-per-use (nur wenn jemand die App nutzt)
- ✅ HTTPS automatisch
- ✅ Keine Server-Verwaltung
- ✅ Bessere Performance als Streamlit Cloud

## Troubleshooting

**Container startet nicht:**
```bash
# Logs prüfen
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=alkosto-ai" --limit=50
```

**Secrets nicht gefunden:**
- Prüfe, ob Umgebungsvariablen gesetzt sind:
```bash
gcloud run services describe alkosto-ai --region us-central1
```
