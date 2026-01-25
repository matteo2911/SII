# import_film_con_id_esistenti.py
from pathlib import Path
import sys
import os
import csv
from datetime import datetime

current_dir = Path(__file__).parent
project_root = current_dir.parent
csv_path = project_root / 'data' / 'movies_con_descrizione_en.csv'
sys.path.append(str(project_root))

from database import db, Film, Genere, Attore, Regista, FilmAttori, FilmGeneri
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(project_root / 'instance' / 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def carica_dizionari():
    """Carica dizionari per conversione nomi->ID"""
    with app.app_context():
        return {
            'regististi': {r.nome: r.id_regista for r in Regista.query.all()},
            'attori': {a.nome: a.id_attore for a in Attore.query.all()},
            'generi': {g.nome: g.id for g in Genere.query.all()}
        }

def importa_film(csv_path):
    dizionari = carica_dizionari()
    
    with app.app_context():
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                total = 0
                successi = 0
                
                for riga in csv_reader:
                    total += 1
                    try:
                        
                        nome_regista = riga['regista'].strip()
                        regista_id = dizionari['regististi'].get(nome_regista)
                        
                        if not regista_id:
                            print(f"Film ID {riga['movieId']}: Regista '{nome_regista}' non trovato, verrà impostato a NULL")
                            regista_id = None  # Imposta esplicitamente a None

                        
                        nuovo_film = Film(
                            movieId=int(riga['movieId']),
                            title=riga['title'].strip(),
                            popolarita=float(riga['popolarita']),
                            descrizione=riga['descrizione'].strip(),
                            descrizione_eng=riga['descrizione_en'].strip(),
                            media_voto=float(riga['media_voti']),
                            anno=int(riga['anno']),
                            url=(riga['poster_url']),
                            tag=(riga['tag']),
                            regista_id=regista_id  # Può essere NULL
                        )
                        db.session.add(nuovo_film)
                        db.session.flush()

                       
                        attori_ids = []
                        for nome_attore in [a.strip() for a in riga['attori'].split(',')]:
                            attore_id = dizionari['attori'].get(nome_attore)
                            if attore_id:
                                attori_ids.append(attore_id)
                            else:
                                print(f"Film ID {riga['movieId']}: Attore '{nome_attore}' non trovato")

                        
                        generi_ids = []
                        for nome_genere in [g.strip() for g in riga['genres'].split('|')]:
                            genere_id = dizionari['generi'].get(nome_genere)
                            if genere_id:
                                generi_ids.append(genere_id)
                            else:
                                print(f"Film ID {riga['movieId']}: Genere '{nome_genere}' non trovato")

                        
                        for attore_id in attori_ids:
                            db.session.add(FilmAttori(
                                movie_id=nuovo_film.movieId,
                                attore_id=attore_id
                            ))

                        for genere_id in generi_ids:
                            db.session.add(FilmGeneri(
                                movie_id=nuovo_film.movieId,
                                genere_id=genere_id
                            ))

                        successi += 1
                        if successi % 50 == 0:
                            db.session.commit()
                            print(f"Elaborati {successi} film...")

                    except Exception as e:
                        print(f"Errore film ID {riga.get('movieId', 'sconosciuto')}: {str(e)}")
                        db.session.rollback()

                db.session.commit()
                print(f"Importazione completata. Successi: {successi}/{total}")

        except Exception as e:
            db.session.rollback()
            print(f"Errore critico: {str(e)}")
            raise

if __name__ == '__main__':
    importa_film(csv_path)