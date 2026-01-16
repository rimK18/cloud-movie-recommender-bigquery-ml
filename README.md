# Movie Recommender – Cloud-Based Recommendation System

A cloud-based movie recommendation system developed as part of the **Cloud & Advanced Analytics 2025** course at **HEC Lausanne**.

The project focuses on the **design and deployment of a full data-driven recommendation pipeline**, combining SQL-based collaborative filtering, BigQuery ML, and containerized cloud services.

---

## Key Features

- Movie search with autocomplete (powered by Elasticsearch)
- Movie selection via interactive UI
- Personalized recommendations based on:
  - User similarity (collaborative filtering using SQL)
  - Matrix factorization model trained with **BigQuery ML**
- Movie posters retrieved via **The Movie Database (TMDB) API**
- Fully containerized services deployed on **Google Cloud Run**

---

## Recommendation Logic

### 1. Personalized Recommendations
When one or more movies are selected:
- The backend identifies **top-k similar users** who rated the same movies highly (`rating_im ≥ 0.8`)
- These user IDs are passed to a **BigQuery ML matrix factorization model**
- Recommendations are generated using `ML.PREDICT`

### 2. Cold Start Strategy
If no movies are selected:
- The system falls back to **globally popular movies**
- Selection criteria:
  - `AVG(rating) ≥ 0.8`
  - `vote_count ≥ 10`

This ensures meaningful recommendations even without prior user input.

---

## Architecture Overview

| Component        | Technology Used                         |
|------------------|------------------------------------------|
| Backend API      | Flask                                   |
| Frontend UI      | Streamlit                               |
| Data Storage     | Google BigQuery                         |
| Recommendation   | BigQuery SQL + BigQuery ML              |
| Autocomplete     | Elasticsearch (Elastic Cloud)           |
| Movie Metadata   | The Movie Database (TMDB) API           |
| Deployment       | Docker + Google Cloud Run               |

---

## Project Structure

movie_recommender_project/
├── backend/
│ ├── app2.py
│ ├── requirements.txt
│ └── Dockerfile
├── frontend/
│ ├── frontend.py
│ ├── requirements.txt
│ └── Dockerfile
├── deploy.sh
├── README.md
└── .gitignore

yaml
Copier le code

> ⚠️ Credentials (`gcp_credentials.json`, `.env`) are used locally only and are intentionally excluded from version control.

---

## Deployment

Deployment is automated via a shell script.

From the root of the project:

```bash
bash deploy.sh

The script performs the following steps:

- Authenticates with **Google Cloud**
- Builds Docker images for both **backend** and **frontend**
- Pushes images to the container registry
- Deploys both services to **Google Cloud Run**


## Academic Context

This project was developed to meet the requirements of the **Cloud & Advanced Analytics** course, with a focus on:

- SQL-based collaborative filtering
- Practical use of **BigQuery ML** for recommendation systems
- Cloud-native application design and deployment

