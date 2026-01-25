from pathlib import Path
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from sentence_transformers import SentenceTransformer

from database import Film, db
from flask import Flask
from sqlalchemy.orm import sessionmaker

current_dir = Path(__file__).parent
project_root = current_dir.parent

# Funzione per creare embedding con all-mpnet-base-v2
def get_embedding(text, model):
    return model.encode(text, convert_to_numpy=True)

def crea_embedding_film(session):
    model = SentenceTransformer('all-mpnet-base-v2')

    films = session.query(Film).all()
    print(f"Totale film trovati: {len(films)}")

    for idx, film in enumerate(films, 1):
        print(f"\n[{idx}/{len(films)}] Processing: {film.title}")

        titolo = film.title or ""
        descrizione = film.descrizione_eng or ""
        anno = str(film.anno) if film.anno else ""
        regista = film.regista.nome if film.regista else ""
        attori = ", ".join([a.nome for a in film.attori]) if film.attori else ""
        generi = ", ".join([g.nome for g in film.generi]) if film.generi else ""

        testo = (
            f"Title: {titolo}. Year: {anno}. "
            f"Director: {regista}. Actors: {attori}. "
            f"Genres: {generi}. Plot: {descrizione}"
            
        )


        embedding_vector = get_embedding(testo, model)
        film.embedding = embedding_vector.tolist()
        session.add(film)

        # Commit ogni 500 film per sicurezza e performance
        if idx % 500 == 0:
            print("Commit intermedio...")
            session.commit()

    print("\nCommit finale...")
    session.commit()
    print("Completato!")

# Setup app e DB
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(project_root / 'instance' / 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    Session = sessionmaker(bind=db.engine)
    session = Session()
    crea_embedding_film(session)
