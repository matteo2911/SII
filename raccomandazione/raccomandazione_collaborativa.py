import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, RatingUtente
import json
from collections import defaultdict
from scipy.sparse import load_npz
from database import db, RatingUtente

#  Caricamento globale della matrice e delle mappature
similarity_sparse = load_npz("data/similarity_matrix_sparse.npz")

with open("data/id_to_index.json", "r") as f:
    id_to_index = json.load(f)

with open("data/index_to_id.json", "r") as f:
    index_to_id = json.load(f)
    index_to_id = {int(k): int(v) for k, v in index_to_id.items()}

def raccomanda_film_per_utente(utente_id, top_n=50):
    # Recupera i film valutati da questo utente dal DB
    rating_records = RatingUtente.query.filter_by(utente_id=utente_id).all()
    if not rating_records:
        print(f"Nessun rating trovato per l'utente con ID {utente_id}.")
        return []

    # Crea un dizionario: movie_id → rating
    rated_movies = {r.movie_id: r.rating for r in rating_records}

    # Calcolo punteggi basati sulla similarità
    scores = defaultdict(float)
    for movie_id, user_rating in rated_movies.items():
        str_movie_id = str(movie_id)
        if str_movie_id not in id_to_index:
            continue

        idx = id_to_index[str_movie_id]
        sim_row = similarity_sparse[idx].toarray().flatten()

        for other_idx, sim_score in enumerate(sim_row):
            if sim_score <= 0:
                continue

            other_movie_id = index_to_id.get(other_idx)
            if other_movie_id is None or other_movie_id in rated_movies:
                continue

            scores[other_movie_id] += sim_score * user_rating

    # Ordina e prendi i top N
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return sorted_scores 
