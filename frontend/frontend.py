import streamlit as st
import pandas as pd
import requests
import os
from google.cloud import bigquery

st.set_page_config(page_title="🎬 Movie Recommender", layout="wide")

# 🔗 URL backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

# Connexion à BigQuery
bq_client = bigquery.Client()

# Requête pour charger les films
def load_movies_from_bigquery():
    query = """
        SELECT movieId, title, genres
        FROM `movie-reco-a2.movie_recommender_a2.movies_a2`
    """
    query_job = bq_client.query(query)
    results = query_job.result()
    return pd.DataFrame([dict(row) for row in results])

movies_df = load_movies_from_bigquery()
title_to_id = dict(zip(movies_df["title"], movies_df["movieId"]))
id_to_genre = dict(zip(movies_df["movieId"], movies_df["genres"]))

if "selected_titles" not in st.session_state:
    st.session_state.selected_titles = []

st.title("🎥 Movie Recommendation App")

# Barre de recherche
search_input = st.text_input("💡 Tape un mot-clé ou laisse vide pour afficher tous les titres.")

# Autocomplete via backend (Elasticsearch)
suggestions = []
try:
    if search_input.strip():
        res = requests.get(f"{BACKEND_URL}/autocomplete", params={"query": search_input})
        if res.status_code == 200:
            suggestions = res.json()
    if not suggestions:
        suggestions = list(title_to_id.keys())
except Exception as e:
    st.error(f"Erreur API : {e}")
    suggestions = list(title_to_id.keys())

# Films sélectionnés
valid_selected_titles = [t for t in st.session_state.selected_titles if t in suggestions]

new_selection = st.multiselect(
    "🎬 Sélectionne un ou plusieurs films que tu aimes",
    options=suggestions,
    default=valid_selected_titles,
    key="selection_widget"
)

for title in new_selection:
    if title not in st.session_state.selected_titles:
        st.session_state.selected_titles.append(title)

# Affichage sélection
if st.session_state.selected_titles:
    st.markdown("### ✅ Films sélectionnés :")
    for film in st.session_state.selected_titles:
        st.markdown(f"- 🎬 **{film}**")

# Bouton reset
if st.button("♻️ Réinitialiser la sélection"):
    st.session_state.selected_titles = []
    st.session_state.pop("selection_widget", None)
    st.rerun()

# Bouton de recommandation
if st.button("🍿 Obtenir des recommandations"):
    selected_ids = [title_to_id.get(t) for t in st.session_state.selected_titles if title_to_id.get(t)]
    try:
        with st.spinner("🔍 Génération des recommandations..."):
            response = requests.post(f"{BACKEND_URL}/recommend", json={"movie_ids": selected_ids})
            if response.status_code == 200:
                data = response.json()
                recommended = data.get("recommended_movies", [])
                posters = data.get("posters", [])

                if not recommended:
                    st.info("Aucune recommandation trouvée. Essaie avec d'autres films.")
                else:
                    st.subheader("🎯 Films recommandés :")
                    for i, movie in enumerate(recommended):
                        if not isinstance(movie, dict):
                            continue
                        movie_id = movie.get("movieId")
                        title = movie.get("title", "Titre inconnu")
                        rating = movie.get("rating")
                        genres = id_to_genre.get(movie_id, "Genres inconnus")
                        poster = posters[i] if i < len(posters) else None

                        with st.container():
                            cols = st.columns([1, 5])
                            with cols[0]:
                                if poster:
                                    st.image(poster, width=140)
                                else:
                                    st.write("🖼️ Pas d'affiche")
                            with cols[1]:
                                st.markdown(f"### 🎬 {title}")
                                st.markdown(f"🆔 ID : {movie_id}")
                                st.markdown(f"📀 Genres : *{genres}*")
                        st.markdown("---")
            else:
                st.warning("Erreur du serveur lors de la génération des recommandations.")
    except Exception as e:
        st.error(f"Erreur API : {e}")

