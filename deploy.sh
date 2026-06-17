#!/usr/bin/env bash
# Déploie le MCP enveloppes sur Cloud Run.
# Build en DEUX étapes (Artifact Registry puis run deploy) — voir les gotchas plus bas.
set -euo pipefail

PROJECT="${PROJECT:-avisia-training}"
REGION="${REGION:-europe-west1}"
SERVICE="${SERVICE:-mcp-enveloppes}"
REPO="cloud-run-source-deploy"
STAGING="gs://avisia-training-cloudbuild-source/source"

TS=$(date +%s)
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/${SERVICE}:dev-${TS}"

echo "▶ Build ${IMAGE}"
# 1) Build du Dockerfile vers Artifact Registry.
#    --region + --gcs-source-staging-dir requis : l'org policy gcp.resourceLocations
#    bloque le bucket `us` par défaut.
gcloud builds submit \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --gcs-source-staging-dir="${STAGING}" \
  --tag "${IMAGE}" .

echo "▶ Deploy ${SERVICE}"
# 2) Deploy de l'image.
#    NE JAMAIS utiliser `gcloud run deploy --source .` ici : ça bascule en Buildpacks
#    et ignore le Dockerfile (image cassée). Toujours --image avec l'étape de build.
#
#    --allow-unauthenticated : nécessaire car /oauth/callback doit être joignable par le
#    navigateur du user. Durcissement prod (MCP privé derrière l'agent host Chat,
#    callback isolé) = étape ultérieure.
#
#    Le secret OAuth vient de Secret Manager (créer : gcloud secrets create
#    enveloppes-oauth-client-secret --data-file=-).
gcloud run deploy "${SERVICE}" \
  --project="${PROJECT}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --allow-unauthenticated \
  --set-env-vars="^@^GOOGLE_CLOUD_PROJECT=${PROJECT}@GOOGLE_OAUTH_CLIENT_ID=${GOOGLE_OAUTH_CLIENT_ID:?définir GOOGLE_OAUTH_CLIENT_ID}@OAUTH_REDIRECT_URI=${OAUTH_REDIRECT_URI:?définir OAUTH_REDIRECT_URI}" \
  --set-secrets="GOOGLE_OAUTH_CLIENT_SECRET=enveloppes-oauth-client-secret:latest"

URL=$(gcloud run services describe "${SERVICE}" --project="${PROJECT}" --region="${REGION}" --format='value(status.url)')
echo "✓ MCP déployé : ${URL}/mcp/"
echo "  ⚠️ Vérifier que OAUTH_REDIRECT_URI = ${URL}/oauth/callback et qu'il est déclaré"
echo "     dans le client OAuth (console GCP). Sinon : 1er deploy pour obtenir l'URL,"
echo "     déclarer le redirect, puis redéployer."
echo "  Connectez le MCP depuis Claude : ${URL}/mcp/"
