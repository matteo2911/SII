import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, RatingUtente
import json
from collections import defaultdict
from scipy.sparse import load_npz
from database import db, RatingUtente, Film, FilmPreferito
from sklearn.preprocessing import MinMaxScaler

def normalizza(dizionario):
    if not dizionario:
        return {}
    values = list(dizionario.values())
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform([[v] for v in values])
    return {k: float(scaled[i][0]) for i, k in enumerate(dizionario)}



# Carica la matrice di similarità
similarity_sparse = load_npz("data/similarity_matrix_sparse.npz")
with open("data/id_to_index.json", "r") as f:
    id_to_index = json.load(f)
with open("data/index_to_id.json", "r") as f:
    index_to_id = {int(k): int(v) for k, v in json.load(f).items()}

# Pesi content-based
PESO_GENERE = 0.5
PESO_REGISTA = 0.3
PESO_ATTORE = 0.2

def costruisci_profilo_utente_pesato(user_id, db_session):
    profilo_generi = defaultdict(float)
    profilo_registi = defaultdict(float)
    profilo_attori = defaultdict(float)

    preferiti = (
        db_session.query(Film)
        .join(FilmPreferito, Film.movieId == FilmPreferito.movie_id)
        .filter(FilmPreferito.utente_id == user_id)
        .all()
    )
    for film in preferiti:
        for g in film.generi:
            profilo_generi[g.id] += 5 * PESO_GENERE
        if film.regista_id:
            profilo_registi[film.regista_id] += 5 * PESO_REGISTA
        for a in film.attori:
            profilo_attori[a.id_attore] += 5 * PESO_ATTORE

    valutati = (
        db_session.query(Film, RatingUtente.rating)
        .join(RatingUtente, Film.movieId == RatingUtente.movie_id)
        .filter(RatingUtente.utente_id == user_id)
        .all()
    )
    for film, rating in valutati:
        for g in film.generi:
            profilo_generi[g.id] += rating * PESO_GENERE
        if film.regista_id:
            profilo_registi[film.regista_id] += rating * PESO_REGISTA
        for a in film.attori:
            profilo_attori[a.id_attore] += rating * PESO_ATTORE

    return profilo_generi, profilo_registi, profilo_attori

def punteggi_collaborativi(user_id):
    rating_records = RatingUtente.query.filter_by(utente_id=user_id).all()
    if not rating_records:
        return {}

    rated_movies = {r.movie_id: r.rating for r in rating_records}
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

    return scores  # {movieId: score}

def punteggi_content_based(user_id, db_session):
    profilo_generi, profilo_registi, profilo_attori = costruisci_profilo_utente_pesato(user_id, db_session)

    film_esclusi_ids = db_session.query(RatingUtente.movie_id).filter_by(utente_id=user_id).all()
    film_esclusi_ids += db_session.query(FilmPreferito.movie_id).filter_by(utente_id=user_id).all()
    film_esclusi_ids = set(f[0] for f in film_esclusi_ids)

    candidati = db_session.query(Film).filter(~Film.movieId.in_(film_esclusi_ids)).all()
    punteggi = {}

    for film in candidati:
        punteggio = 0.0
        punteggio += sum(profilo_generi.get(g.id, 0) for g in film.generi)
        if film.regista_id:
            punteggio += profilo_registi.get(film.regista_id, 0)
        punteggio += sum(profilo_attori.get(a.id_attore, 0) for a in film.attori)
        if punteggio > 0:
            punteggi[film.movieId] = punteggio

    return punteggi  # {movieId: score}

def raccomanda_film_ibrido(user_id, db_session, alpha=0.5, top_n=50):
    # Recupera punteggi
    score_collab_raw = punteggi_collaborativi(user_id)
    score_content_raw = punteggi_content_based(user_id, db_session)

    # Normalizza i punteggi per renderli comparabili
    score_collab = normalizza(score_collab_raw)
    score_content = normalizza(score_content_raw)

    # Unione dei punteggi (pesata)
    all_movie_ids = set(score_collab.keys()).union(score_content.keys())
    final_scores = {}
    for movie_id in all_movie_ids:
        sc = score_collab.get(movie_id, 0.0)
        ct = score_content.get(movie_id, 0.0)
        final_scores[movie_id] = alpha * sc + (1 - alpha) * ct

    # Ordina e ritorna i top N
    sorted_scores = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    film_ids = [movie_id for movie_id, _ in sorted_scores]

    # Recupera gli oggetti Film finali ordinati
    film_ordinati = db_session.query(Film).filter(Film.movieId.in_(film_ids)).all()
    film_dict = {f.movieId: f for f in film_ordinati}

    return [film_dict[mid] for mid in film_ids if mid in film_dict]

