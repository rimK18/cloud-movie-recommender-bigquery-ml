from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
from google.cloud import bigquery
from dotenv import load_dotenv
import requests
import os

# 🔧 Charger les variables d'environnement
load_dotenv()
print("🔐 TMDB_API_KEY:", os.getenv("TMDB_API_KEY"))
if os.getenv("ENV") != "production":
    gcp_creds_path = os.path.join(os.path.dirname(__file__), "gcp_credentials.json")
    if os.path.exists(gcp_creds_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_creds_path
        print("✅ Credentials GCP chargés depuis le fichier local.")
    else:
        print("⚠️ Avertissement : gcp_credentials.json introuvable, l'accès à BigQuery peut échouer en local.")

#  Initialiser Flask
app = Flask(__name__)

# Connexions Elasticsearch et BigQuery
es = Elasticsearch(os.getenv("ES_ENDPOINT"), api_key=os.getenv("ES_API_KEY"))
bq_client = bigquery.Client()

#  TMDB
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

#  Autocomplete
@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])

    try:
        res = es.search(index="movies", body={
            "query": {
                "match_phrase_prefix": {
                    "title": {
                        "query": query
                    }
                }
            }
        })
        movies = [hit['_source']['title'] for hit in res['hits']['hits']]
        return jsonify(movies)
    except Exception as e:
        print("Erreur Elasticsearch:", e)
        return jsonify([])

#  Recommandation
@app.route('/recommend', methods=['POST'])
def recommend():
    print("✅ Requête reçue sur /recommend")
    data = request.get_json()
    movie_ids = data.get('movie_ids', [])

    if not isinstance(movie_ids, list):
        return jsonify({"error": "movie_ids must be a list"}), 400

    try:
        recommended_movies = get_recommendations(movie_ids)

        if all(isinstance(m, str) for m in recommended_movies):
            print("⚠️ Fallback: conversion str → dict")
            recommended_movies = [
                {"title": m.strip('"'), "movieId": None, "tmdbId": None, "rating": None}
                for m in recommended_movies
            ]

        posters = get_movie_posters(recommended_movies)

        return jsonify({
            "recommended_movies": recommended_movies,
            "posters": posters
        })
    except Exception as e:
        print("Erreur backend:", e)
        return jsonify({"error": "Erreur lors du traitement"}), 500

# Recommandations via reco_model avec similarité utilisateur
def get_recommendations(movie_ids):
    print("🎯 DEBUG: Lancement get_recommendations avec :", movie_ids)

    if not movie_ids:
        query = """
        SELECT 
            m.movieId, 
            m.title, 
            l.tmdbId,
            AVG(r.rating_im) AS avg_rating, 
            COUNT(r.userId) AS vote_count
        FROM `movie-reco-a2.movie_recommender_a2.ratings_a2` r
        JOIN `movie-reco-a2.movie_recommender_a2.movies_a2` m ON r.movieId = m.movieId
        JOIN `movie-reco-a2.movie_recommender_a2.links_a2` l ON m.movieId = l.movieId
        WHERE l.tmdbId IS NOT NULL
        GROUP BY m.movieId, m.title, l.tmdbId
        HAVING vote_count >= 10 AND avg_rating >= 0.8
        ORDER BY avg_rating DESC
        LIMIT 10
        """
    else:
        movie_id_str = ', '.join(map(str, movie_ids))
        query = f"""
        DECLARE user_selected_movies ARRAY<INT64>;
        SET user_selected_movies = [{movie_id_str}];

        WITH similar_users AS (
            SELECT userId
            FROM `movie-reco-a2.movie_recommender_a2.ratings_a2`
            WHERE movieId IN UNNEST(user_selected_movies)
              AND rating_im >= 0.8
            GROUP BY userId
            ORDER BY COUNT(*) DESC
            LIMIT 10
        ),
        candidate_movies AS (
            SELECT DISTINCT movieId
            FROM `movie-reco-a2.movie_recommender_a2.ratings_a2`
            WHERE movieId NOT IN UNNEST(user_selected_movies)
        ),
        predictions AS (
            SELECT
                predicted.userId,
                predicted.movieId,
                predicted.predicted_rating_im_confidence AS rating
            FROM
                ML.PREDICT(MODEL `movie-reco-a2.movie_recommender_a2.reco_model`,
                  (
                    SELECT userId, movieId
                    FROM similar_users, candidate_movies
                  )
                ) AS predicted
        ),
        aggregated AS (
            SELECT movieId, AVG(rating) as avg_rating
            FROM predictions
            GROUP BY movieId
            ORDER BY avg_rating DESC
            LIMIT 10
        )
        SELECT m.movieId, m.title, l.tmdbId, a.avg_rating
        FROM aggregated a
        JOIN `movie-reco-a2.movie_recommender_a2.movies_a2` m ON a.movieId = m.movieId
        JOIN `movie-reco-a2.movie_recommender_a2.links_a2` l ON m.movieId = l.movieId
        WHERE l.tmdbId IS NOT NULL
        """

    query_job = bq_client.query(query)
    results = query_job.result()

    print("✅ Résultats bruts de BigQuery reçus")

    formatted = []
    for row in results:
        try:
            film = {
                "title": row.title,
                "movieId": row.movieId,
                "tmdbId": row.tmdbId,
                "rating": float(row.avg_rating) if hasattr(row, "avg_rating") and row.avg_rating is not None else None
            }
            print("✅ Film formaté :", film)
            formatted.append(film)
        except Exception as e:
            print("⚠️ Erreur de parsing ligne :", e, row)
            formatted.append({
                "title": str(row),
                "movieId": None,
                "tmdbId": None,
                "rating": None
            })

    return formatted

# Récupération des affiches TMDB
def get_movie_posters(movies):
    DEFAULT_POSTER = "https://via.placeholder.com/300x450.png?text=Aucune+affiche"
    posters = []

    for movie in movies:
        tmdb_id = movie.get("tmdbId")
        if not tmdb_id:
            posters.append(DEFAULT_POSTER)
            continue

        try:
            response = requests.get(
                f"{TMDB_BASE_URL}/movie/{tmdb_id}",
                params={"api_key": TMDB_API_KEY},
                timeout=5
            )

            if response.status_code != 200:
                print(f"❌ TMDB {tmdb_id} → status: {response.status_code}")
                posters.append(DEFAULT_POSTER)
                continue

            data = response.json()
            poster_path = data.get("poster_path")

            if poster_path and isinstance(poster_path, str):
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                posters.append(poster_url)
            else:
                print(f"ℹ️ TMDB {tmdb_id} → pas d’affiche")
                posters.append(DEFAULT_POSTER)

        except Exception as e:
            print(f"⚠️ Erreur TMDB pour ID {tmdb_id}:", e)
            posters.append(DEFAULT_POSTER)

    return posters

# Lancement serveur Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
