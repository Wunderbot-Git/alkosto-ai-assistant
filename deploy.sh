#!/bin/bash
# Alkosto AI Assistant - Google Cloud Run Deploy Script
# Dieses Skript deployt die App automatisch

set -e  # Stop bei Fehlern

echo "🚀 Alkosto AI Assistant - Cloud Run Deploy"
echo "============================================"
echo ""

# Konfiguration
PROJECT_ID="alkosto-ai-agent"
SERVICE_NAME="alkosto-ai"
REGION="us-central1"
IMAGE_TAG="latest"

# API Keys (werden als Secrets verwendet)
GEMINI_API_KEY="AIzaSyDipHWslKl1AFFc959vxk4yFRTsgVl4ROM"
ALGOLIA_API_KEY="a0e524e91a99723b11a1ea7bab1e504a"

echo "📋 Konfiguration:"
echo "  Projekt: $PROJECT_ID"
echo "  Service: $SERVICE_NAME"
echo "  Region: $REGION"
echo ""

# Prüfe ob gcloud installiert ist
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud nicht gefunden. Installiere Google Cloud SDK..."
    
    # Installiere gcloud
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -sSL https://sdk.cloud.google.com | bash
        export PATH="$HOME/google-cloud-sdk/bin:$PATH"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install google-cloud-sdk
    else
        echo "❌ Unbekanntes Betriebssystem. Bitte manuell installieren:"
        echo "   https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
fi

echo "✅ gcloud gefunden"

# Login (falls nicht bereits eingeloggt)
echo ""
echo "🔐 Prüfe Google Cloud Login..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "Bitte melde dich bei Google Cloud an:"
    gcloud auth login
fi

# Projekt setzen
echo ""
echo "📁 Setze Projekt: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Aktiviere APIs
echo ""
echo "🔧 Aktiviere Cloud Run API..."
gcloud services enable run.googleapis.com containerregistry.googleapis.com

# Gehe zum Projektverzeichnis
echo ""
echo "📂 Wechsle zum Projektverzeichnis..."
cd "$(dirname "$0")"

# Baue Docker Image
echo ""
echo "🐳 Baue Docker Image..."
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG .

# Push zu Google Container Registry
echo ""
echo "⬆️  Pushe Image zu Google Container Registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG

# Deploy zu Cloud Run
echo ""
echo "🚀 Deploy zu Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
  --set-env-vars ALGOLIA_API_KEY=$ALGOLIA_API_KEY \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --timeout 300

# Zeige URL
echo ""
echo "✅ Deployment erfolgreich!"
echo ""
URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo "🌐 Deine App läuft unter:"
echo "   $URL"
echo ""
echo "📊 Monitoring:"
echo "   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics"
echo ""

# Optional: Öffne im Browser
read -p "Im Browser öffnen? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$URL"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        open "$URL"
    fi
fi

echo ""
echo "🎉 Fertig! Viel Spaß mit deinem Alkosto AI Assistant!"
