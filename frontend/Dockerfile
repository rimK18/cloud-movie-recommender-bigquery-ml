# syntax=docker/dockerfile:1

#  Base image AMD64 (Mac M1 fix)
FROM --platform=linux/amd64 python:3.10-slim

#  Dossier de travail
WORKDIR /app

#  Installer dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#  Code source
COPY . .

#  Port pour Streamlit sur Cloud Run
EXPOSE 8080

#  Lancer Streamlit sur le bon port Cloud Run
CMD ["streamlit", "run", "frontend.py", "--server.port=8080", "--server.address=0.0.0.0"]
