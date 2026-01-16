#!/bin/bash

#  Paramètres de déploiement
PROJECT_ID="movie-reco-a2"
REGION="europe-west6"
REPO="movie-repo"
BACKEND_NAME="movie-backend"
FRONTEND_NAME="movie-frontend"

#  Authentification gcloud
echo " Connexion à Google Cloud..."
gcloud auth login
gcloud config set project $PROJECT_ID

# Créer le repository Artifact Registry s'il n'existe pas
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --description="Repo Docker pour l'application de recommandation" || echo " Repo déjà existant"

# Authentifier Docker avec Artifact Registry
gcloud auth configure-docker $REGION-docker.pkg.dev

# 🔨 Activer buildx si ce n’est pas encore fait
docker buildx create --use || echo " buildx déjà actif"

# Dockeriser le BACKEND
echo "Dockerisation BACKEND..."
cd backend
docker buildx build --platform=linux/amd64 -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend . --push
cd ..

#  Dockeriser le FRONTEND
echo " Dockerisation FRONTEND..."
cd frontend
docker buildx build --platform=linux/amd64 -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend . --push
cd ..

# Déploiement BACKEND sur Cloud Run
echo " Déploiement BACKEND..."
gcloud run deploy $BACKEND_NAME \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --set-env-vars="ENV=production,TMDB_API_KEY=045cfc313f4083174f4bad214f648341,ES_ENDPOINT=https://f1edd1ae6a2b42d991b9135b74e5ab0d.us-central1.gcp.cloud.es.io:443,ES_API_KEY=dqWaQC0WQx-Rl8riTaCAVA"

# Récupérer l'URL du backend
BACKEND_URL=$(gcloud run services describe $BACKEND_NAME --platform=managed --region=$REGION --format="value(status.url)")

# Déploiement FRONTEND sur Cloud Run
echo " Déploiement FRONTEND..."
gcloud run deploy $FRONTEND_NAME \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --set-env-vars="BACKEND_URL=$BACKEND_URL"

#  Résumé final
echo ""
echo " Déploiement terminé avec succès !"
echo " Backend URL  : $BACKEND_URL"
echo " Frontend URL : $(gcloud run services describe $FRONTEND_NAME --platform=managed --region=$REGION --format='value(status.url)')"

