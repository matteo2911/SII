import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import numpy as np
from scipy.sparse import load_npz, csr_matrix

from database import RatingUtente


# --- Caricamenti globali dal CSV preprocessato ---
user_item_sparse = load_npz("data/user_item_matrix_sparse.npz")  # (n_users_csv x n_movies_csv)
user_norms = np.load("data/user_norms.npy")                      # (n_users_csv,)

with open("data/movie_id_to_index.json", "r") as f:
    movie_id_to_index = json.load(f)  # str(movieId) -> col_index

with open("data/movie_index_to_id.json", "r") as f:
    movie_index_to_id = json.load(f)  # col_index(str) -> movieId
    movie_index_to_id = {int(k): int(v) for k, v in movie_index_to_id.items()}


def raccomanda_film_per_utente_user_based(utente_id, top_n=50):
    # 1) Rating utente attuale dal DB
    rating_records = RatingUtente.query.filter_by(utente_id=utente_id).all()
    if not rating_records:
        print(f"Nessun rating trovato per l'utente con ID {utente_id}.")
        return []

    # 2) Costruisci vettore utente nello spazio film del CSV
    cols = []
    data = []
    for r in rating_records:
        col_idx = movie_id_to_index.get(str(r.movie_id))
        if col_idx is None:
            continue
        cols.append(int(col_idx))
        data.append(float(r.rating))

    if not cols:
        print(f"Nessun film dell'utente {utente_id} presente nel mapping movie_id_to_index (CSV).")
        return []

    n_movies = user_item_sparse.shape[1]
    user_vec = csr_matrix((data, ([0] * len(cols), cols)), shape=(1, n_movies))

    # 3) Similarità cosine tra utente attuale e tutti gli utenti del CSV
    # dots: (n_users_csv x n_movies) dot (n_movies x 1) -> (n_users_csv x 1)
    dots = user_item_sparse.dot(user_vec.T).toarray().ravel()

    user_norm = float(np.sqrt(np.sum(np.square(data))))
    if user_norm <= 0:
        return []

    denom = user_norms * user_norm
    sims = np.zeros_like(dots, dtype=float)

    mask = denom > 0
    sims[mask] = dots[mask] / denom[mask]

    # stessa soglia che usi nella costruzione della matrice
    sims[sims < 0.1] = 0.0

    if np.count_nonzero(sims) == 0:
        return []

    # 4) Punteggio film: sims^T * user_item_sparse  -> (1 x n_movies)
    sim_row = csr_matrix(sims.reshape(1, -1))
    score_row = sim_row.dot(user_item_sparse).toarray().ravel()

    # 5) Escludi film già votati dall'utente
    score_row[np.array(cols, dtype=int)] = -np.inf

    # 6) Top-N (ritorna (movie_id, score))
    order = np.argsort(-score_row)

    risultati = []
    for j in order:
        if len(risultati) >= top_n:
            break

        s = float(score_row[j])
        if s == -np.inf or s <= 0:
            continue

        movie_id = movie_index_to_id.get(int(j))
        if movie_id is None:
            continue

        risultati.append((movie_id, s))

    return risultati
