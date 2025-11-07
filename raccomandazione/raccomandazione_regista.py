from database import Film, RegistaPreferito, Regista
from sqlalchemy.orm import joinedload

def raccomanda_film_per_registi(user_id, db_session, limite=10):

    # Recupera i registi preferiti dell'utente
    registi_preferiti = (
        db_session.query(RegistaPreferito.regista_id)
        .filter_by(utente_id=user_id)
        .all()
    )
    registi_preferiti_ids = [r.regista_id for r in registi_preferiti]

    if not registi_preferiti_ids:
        return []

    # Recupera i film associati ai registi preferiti, ordinati per popolarità
    film_raccomandati = (
        db_session.query(Film)
        .filter(Film.regista_id.in_(registi_preferiti_ids))
        .options(joinedload(Film.regista))  # Caricamento eager del regista
        .order_by(Film.popolarita.desc())
        .limit(limite)
        .all()
    )

    print("Raccomandazione per regista")

    return film_raccomandati
