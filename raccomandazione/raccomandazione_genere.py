from database import Film, GeneriPreferiti, FilmGeneri, Genere
from sqlalchemy.orm import joinedload

def raccomanda_film_per_generi(user_id, db_session, limite=10):

    # Recupera i generi preferiti dell'utente
    generi_preferiti = db_session.query(GeneriPreferiti.genere).filter_by(utente_id=user_id).all()
    generi_preferiti = [g.genere for g in generi_preferiti]

    if not generi_preferiti:
        return []

    # Recupera i film associati ai generi preferiti, ordinati per popolarità
    film_raccomandati = (
        db_session.query(Film).join(FilmGeneri, Film.movieId == FilmGeneri.movie_id)
        .join(Genere, FilmGeneri.genere_id == Genere.id)
        .filter(Genere.nome.in_(generi_preferiti))
        .options(joinedload(Film.generi))  # Caricamento dei generi per evitare query aggiuntive
        .order_by(Film.popolarita.desc())
        .limit(limite)
        .all()
    )

    print("raccomandazione per genere")

    return film_raccomandati