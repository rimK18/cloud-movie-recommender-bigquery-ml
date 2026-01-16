# syntax=docker/dockerfile:1

#  Base image avec architecture AMD64 (pour Cloud Run)
FROM --platform=linux/amd64 python:3.10-slim

#  Fix compatibilité Cloud Run
ENV DOCKER_CREDENTIALS_STORE=""
ENV PORT=8080

#  Dossier de travail
WORKDIR /app

#  Dépendances
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

#  Code source
COPY . .

#  Port exposé (Cloud Run = 8080)
EXPOSE 8080

#  Lancement de l’app Flask
CMD ["python", "app2.py"]
