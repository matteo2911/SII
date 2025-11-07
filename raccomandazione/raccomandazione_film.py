from sqlalchemy.orm import subqueryload

from database import Film, FilmGeneri, FilmPreferito, RatingUtente
from raccomandazione.raccomandazione_ibrida import costruisci_profilo_utente_pesato

def raccomanda_film_per_film(user_id, db_session, limite=10):
    profilo_generi, profilo_registi, profilo_attori = costruisci_profilo_utente_pesato(user_id, db_session)

    # Film già visti o preferiti
    film_esclusi_ids = db_session.query(RatingUtente.movie_id).filter_by(utente_id=user_id).all()
    film_esclusi_ids += db_session.query(FilmPreferito.movie_id).filter_by(utente_id=user_id).all()
    film_esclusi_ids = set(f[0] for f in film_esclusi_ids)

    # Film candidati filtrati solo per generi del profilo
    generi_ids = list(profilo_generi.keys())
    film_ids_candidati = (
        db_session.query(FilmGeneri.movie_id)
        .filter(FilmGeneri.genere_id.in_(generi_ids))
        .distinct()
        .all()
    )
    film_ids_candidati = [fid[0] for fid in film_ids_candidati if fid[0] not in film_esclusi_ids]

    # Caricamento dei film selezionati con dati collegati
    candidati = (
        db_session.query(Film)
        .filter(Film.movieId.in_(film_ids_candidati))
        .options(subqueryload(Film.generi), subqueryload(Film.attori))
        .all()
    )

    risultati = []
    for film in candidati:
        punteggio = 0.0
        punteggio += sum(profilo_generi.get(g.id, 0) for g in film.generi)
        if film.regista_id:
            punteggio += profilo_registi.get(film.regista_id, 0)
        punteggio += sum(profilo_attori.get(a.id_attore, 0) for a in film.attori)

        if punteggio > 0:
            risultati.append((film, punteggio))

    risultati.sort(key=lambda x: x[1], reverse=True)
    return [film for film, _ in risultati[:limite]]
