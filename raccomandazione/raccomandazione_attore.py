from database import Film, AttorePreferito, FilmAttori, Attore
from sqlalchemy.orm import joinedload

def raccomanda_film_per_attori(user_id, db_session, limite=10):

    # Recupera gli attori preferiti dell'utente
    attori_preferiti = (
        db_session.query(AttorePreferito.attore_id)
        .filter_by(utente_id=user_id)
        .all()
    )
    attori_preferiti_ids = [a.attore_id for a in attori_preferiti]

    if not attori_preferiti_ids:
        return []

    # Recupera i film associati agli attori preferiti, ordinati per popolarità
    film_raccomandati = (
        db_session.query(Film)
        .join(FilmAttori, Film.movieId == FilmAttori.movie_id)
        .filter(FilmAttori.attore_id.in_(attori_preferiti_ids))
        .options(joinedload(Film.attori))  # Caricamento eager degli attori
        .order_by(Film.popolarita.desc())
        .limit(limite)
        .all()
    )

    print("Raccomandazione per attore")

    return film_raccomandati