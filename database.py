import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import JSON
 
 
db = SQLAlchemy()
 
# -------------------- MODELLI DB --------------------
 
class Utente(db.Model):
    __tablename__ = 'utenti_registrati'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
 
   
    def set_password(self, password):
        self.password = generate_password_hash(password)
 
    def check_password(self, password):
        return check_password_hash(self.password, password)
 
class FilmPreferito(db.Model):
    __tablename__ = 'film_preferiti'
    utente_id = db.Column(db.Integer, db.ForeignKey('utenti_registrati.id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('film.movieId'), primary_key=True)  
 
    # Relazione con il modello Film
    film = db.relationship('Film', backref='preferiti', lazy=True)
 
   
 
class RatingUtente(db.Model):
    __tablename__ = 'rating_utente'
    utente_id = db.Column(db.Integer, db.ForeignKey('utenti_registrati.id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('film.movieId'), primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    film = db.relationship('Film', backref='ratings', lazy=True)
   
class Attore(db.Model):
    __tablename__ = 'attori'
    id_attore = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
 
    preferenze = db.relationship('AttorePreferito', backref='attore', lazy=True)
 
class Regista(db.Model):
    __tablename__ = 'registi'
    id_regista = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
   
    preferenze = db.relationship('RegistaPreferito', backref='regista', lazy=True)
 
class AttorePreferito(db.Model):
    __tablename__ = 'attori_preferiti'
    utente_id = db.Column(db.Integer, db.ForeignKey('utenti_registrati.id'), primary_key=True)
    attore_id = db.Column(db.Integer, db.ForeignKey('attori.id_attore'), primary_key=True)
 
    utente = db.relationship('Utente', backref='attori_preferiti', lazy=True)
 
class RegistaPreferito(db.Model):
    __tablename__ = 'registi_preferiti'
    utente_id = db.Column(db.Integer, db.ForeignKey('utenti_registrati.id'), primary_key=True)
    regista_id = db.Column(db.Integer, db.ForeignKey('registi.id_regista'), primary_key=True)
 
class GeneriPreferiti(db.Model):
    __tablename__ = 'generi_preferiti'
    utente_id = db.Column(db.Integer, db.ForeignKey('utenti_registrati.id'), primary_key=True)
    genere = db.Column(db.String(50), primary_key=True)
 
 
 
class Genere(db.Model):
    __tablename__ = 'generi'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
 
class Film(db.Model):
    __tablename__ = 'film'
    movieId = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    popolarita = db.Column(db.Float)
    descrizione = db.Column(db.Text)
    descrizione_eng=db.Column(db.Text)
    media_voto = db.Column(db.Float)
    anno = db.Column(db.Integer)
    url=db.Column(db.String)
    embedding = db.Column(JSON, nullable=True)
    tag = db.Column(db.String)
   
    # Relazione con Regista (uno-a-molti)
    regista_id = db.Column(db.Integer, db.ForeignKey('registi.id_regista'), nullable=True)
    regista = db.relationship('Regista', backref='film')
   
    # Relazione molti-a-molti con Attori (tabella di collegamento)
    attori = db.relationship(
        'Attore',
        secondary='film_attori',
        backref=db.backref('film', lazy='dynamic')
    )
   
    # Relazione molti-a-molti con Generi (tabella di collegamento)
    generi = db.relationship(
        'Genere',
        secondary='film_generi',
        backref=db.backref('film', lazy='dynamic')
    )
 
# Tabella di collegamento per Attori-Film
class FilmAttori(db.Model):
    __tablename__ = 'film_attori'
    movie_id = db.Column(db.Integer, db.ForeignKey('film.movieId'), primary_key=True)
    attore_id = db.Column(db.Integer, db.ForeignKey('attori.id_attore'), primary_key=True)
 
# Tabella di collegamento per Generi-Film
class FilmGeneri(db.Model):
    __tablename__ = 'film_generi'
    movie_id = db.Column(db.Integer, db.ForeignKey('film.movieId'), primary_key=True)
    genere_id = db.Column(db.Integer, db.ForeignKey('generi.id'), primary_key=True)
# -------------------- INIZIALIZZA DB --------------------
 
 
 
 
 
 
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()