import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import warnings
warnings.filterwarnings("ignore")
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)
import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from core.community_structure.Users_community import crea_community_utenti
from core.community_structure.Users_community import calcola_similarita
from core.community_structure.Users_community import visualizza_grafo
from core.search_engine.Attori_Search_Engine import cerca_attore
from core.search_engine.Title_Search_Engine import cerca_film_per_titolo, cerca_film_per_titolo_form
from core.search_engine.Genres_Search_Engine import cerca_film_per_genere
from core.NPLSystem.NPL import cerca_film_simili
from sqlalchemy import inspect
from database import FilmGeneri, Genere, Attore, Film, Regista, db, init_db, Utente, FilmPreferito, GeneriPreferiti, RegistaPreferito, AttorePreferito, RatingUtente
import csv
import matplotlib.pyplot as plt
import networkx as nx 
from raccomandazione import raccomandazione_genere
from sqlalchemy.orm import sessionmaker
from flask import request, render_template
from flask import request, session, render_template, redirect, flash
from raccomandazione.raccomandazione_film import raccomanda_film_per_film
from raccomandazione.raccomandazione_genere import raccomanda_film_per_generi
from raccomandazione.raccomandazione_regista import raccomanda_film_per_registi
from raccomandazione.raccomandazione_attore import raccomanda_film_per_attori
from raccomandazione.raccomandazione_collaborativa import raccomanda_film_per_utente  # Raccomandazione collaborativa
from raccomandazione.raccomandazione_ibrida import raccomanda_film_ibrido  # <-- import ibrido
from sqlalchemy.orm import sessionmaker
from database import db, Film
from flask import request, jsonify
from sqlalchemy.orm import sessionmaker
from database import db, Film
from raccomandazione.raccomandazione_collaborativa import raccomanda_film_per_utente  
from core.community_structure.Genres_community_Structure import genera_immagine_community_generi
from raccomandazione.raccomandazione_collaborativa_user import *



app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)

# -------------------- FUNZIONI UTILI --------------------
def get_user_data():
    if 'user_id' in session:
        user = Utente.query.get(session['user_id'])
        if user:
            generi = [gp.genere for gp in GeneriPreferiti.query.filter_by(utente_id=user.id).all()]
            film = [fp.film.title for fp in FilmPreferito.query.join(Film, FilmPreferito.movie_id == Film.movieId).filter(FilmPreferito.utente_id == user.id).all()]
            registi = [r.id_regista for r in Regista.query.join(RegistaPreferito).filter(RegistaPreferito.utente_id == session['user_id']).all()]
            ratings = RatingUtente.query.filter_by(utente_id=user.id).join(Film).all()
            attori = [a.id_attore for a in Attore.query.join(AttorePreferito).filter(AttorePreferito.utente_id == session['user_id']).all()]
            return {
                'id': user.id,
                'nome': user.nome,
                'cognome': user.cognome,
                'email': user.email,
                'preferiti': {
                    'generi': generi,
                    'titolo': film,
                    'registi': registi,
                    'ratings': ratings,
                    'attori': attori
                }
            }
    return None


# -------------------- OPERAZIONI BASE --------------------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Utente.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            return redirect(url_for('user_page'))
        else:
            flash('Credenziali errate, prova di nuovo!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            nome = request.form['nome']
            cognome = request.form['cognome']
            email = request.form['email']
            password = request.form['password']

            existing_user = Utente.query.filter_by(email=email).first()
            if existing_user:
                flash('Email già registrata!', 'error')
                return redirect('/register')

            new_user = Utente(nome=nome, cognome=cognome, email=email)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash('Registrazione completata con successo!', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f"Errore: {str(e)}", 'error')
            print(f"Errore durante la registrazione: {str(e)}")
            return redirect('/register')

    return render_template('register.html')



@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    return redirect(url_for('home'))


#--------------FUNZIONALITA'---------------------------

@app.route('/user', methods=['GET'])
def user_page():
    if 'user_id' not in session:
        flash('Devi effettuare il login', 'warning')
        return redirect('/login')

    user_data = get_user_data()
    user_id = session['user_id']

    raccomandazioni_genere = []
    raccomandazioni_regista = []
    raccomandazioni_attore = []
    raccomandazioni_film = []
    raccomandazioni_collaborative = []
    raccomandazioni_user_based = [] 
    raccomandazioni_ibrido = []  

    # Raccomandazioni per generi
    if user_data['preferiti']['generi']:
        raccomandazioni_genere = raccomanda_film_per_generi(
            user_id, db.session, limite=50
        )

    # Raccomandazioni per regista
    if user_data['preferiti']['registi']:
        raccomandazioni_regista = raccomanda_film_per_registi(
            user_id, db.session, limite=50
        )

    # Raccomandazioni per attore
    if user_data['preferiti']['attori']:
        raccomandazioni_attore = raccomanda_film_per_attori(
            user_id, db.session, limite=50
        )

    # Raccomandazioni content-based
    if (
        user_data['preferiti']['generi']
        or user_data['preferiti']['registi']
        or user_data['preferiti']['attori']
    ):
        raccomandazioni_film = raccomanda_film_per_film(
            user_id, db.session, limite=50
        )

    # Raccomandazioni collaborative
    try:
        raccomandazioni_collaborative = raccomanda_film_per_utente(user_id, top_n=50)
        movie_ids = [movie_id for movie_id, _ in raccomandazioni_collaborative]
        film_oggetti = db.session.query(Film).filter(Film.movieId.in_(movie_ids)).all()
        film_dict = {f.movieId: f for f in film_oggetti}
        raccomandazioni_collaborative = [film_dict[mid] for mid in movie_ids if mid in film_dict]
    except Exception as e:
        print(f"Errore nella raccomandazione collaborativa: {e}")
        raccomandazioni_collaborative = []

    
    # Raccomandazioni user-based
    try:
        raccomandazioni_user_based = raccomanda_film_per_utente_user_based(user_id, top_n=50)
        movie_ids = [movie_id for movie_id, _ in raccomandazioni_user_based]
        film_oggetti = db.session.query(Film).filter(Film.movieId.in_(movie_ids)).all()
        film_dict = {f.movieId: f for f in film_oggetti}
        raccomandazioni_user_based = [film_dict[mid] for mid in movie_ids if mid in film_dict]
    except Exception as e:
        print(f"Errore nella raccomandazione user-based: {e}")
        raccomandazioni_user_based = []



    # Raccomandazioni ibride
    try:
        raccomandazioni_ibrido = raccomanda_film_ibrido(user_id, db.session, alpha=0.5, top_n=50)
    except Exception as e:
        print(f"Errore nella raccomandazione ibrida: {e}")
        raccomandazioni_ibrido = []

    return render_template(
        'user.html',
        user=user_data,
        film_raccomandati_genere=raccomandazioni_genere,
        film_raccomandati_regista=raccomandazioni_regista,
        film_raccomandati_attore=raccomandazioni_attore,
        film_raccomandati_film=raccomandazioni_film,
        film_raccomandati_collaborativi=raccomandazioni_collaborative,
        film_raccomandati_user_based=raccomandazioni_user_based, 
        film_raccomandati_ibridi=raccomandazioni_ibrido,  # <--- passaggio dati alla view
    )





@app.route('/profilo')
def profilo():
    if 'user_id' not in session:
        flash('Per favore accedi per visualizzare il profilo', 'warning')
        return redirect('/login')

    user_data = get_user_data()
    if not user_data:
        flash('Sessione scaduta o utente non trovato', 'error')
        return redirect('/login')

    # Recupera gli attori preferiti dell'utente
    attoriPreferiti = Attore.query.join(AttorePreferito).filter(AttorePreferito.utente_id == session['user_id']).all()
    registiPreferiti = Regista.query.join(RegistaPreferito).filter(RegistaPreferito.utente_id == session['user_id']).all()
    filmPreferiti = Film.query.join(FilmPreferito, Film.movieId == FilmPreferito.movie_id).filter(FilmPreferito.utente_id == session['user_id']).all()
    filmValutati = db.session.query(RatingUtente,Film.title,Film.movieId).join(Film, Film.movieId == RatingUtente.movie_id).filter(RatingUtente.utente_id == session['user_id']).all()

    return render_template('profilo.html', user=user_data, attoriPreferiti=attoriPreferiti, registiPreferiti=registiPreferiti, filmPreferiti=filmPreferiti, filmValutati=filmValutati)


#-------------------RICERCA----------------------

@app.route('/ricercaGenere', methods=['GET', 'POST'])
def ricerca_genere():
    if 'user_id' not in session:
        return redirect('/login')

    risultati = None
    if request.method == 'POST':
        genere = request.form['genere']
        risultati = cerca_film_per_genere(genere)

    return render_template('ricercaGenere.html', risultati=risultati)



@app.route('/ricercaTitolo', methods=['GET'])
def ricercaTitolo():
    titolo_query = request.args.get('titolo', '').strip()
    risultati = []

    if titolo_query:
        # Recupera i film che corrispondono al titolo
        risultati = (
            db.session.query(Film.movieId, Film.title, Film.url, db.func.group_concat(Genere.nome, ', ').label('genres'))
            .join(FilmGeneri, Film.movieId == FilmGeneri.movie_id)  # Unisce la tabella FilmGeneri
            .join(Genere, FilmGeneri.genere_id == Genere.id)  # Unisce la tabella Genere
            .filter(Film.title.ilike(f"%{titolo_query}%"))  # Filtra per titolo
            .group_by(Film.movieId)  # Raggruppa per film
            .limit(75)
            .all()
        )

    # Passa i risultati al template
    return render_template('ricercaTitolo.html', risultati=[
        {
            'movieId': row[0],
            'title': row[1],
            'url': row[2],
            'genres': row[3],
        }
        for row in risultati
    ])


#---------------------FORM PREFERENZE---------------------


@app.route('/form_preferenze_genere', methods=['GET', 'POST'])
def form_preferenze_genere():
    if 'user_id' not in session:
        return redirect('/login')

    generi_disponibili = ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi', 'Thriller',
                          'Animation', 'Fantasy', 'Documentary', 'Western', 'Children', 'Film-Noir',
                          'Mystery', 'Crime', 'War', 'Adventure', 'Musical', 'IMAX']
    
    if request.method == 'POST':
        generi_selezionati = request.form.getlist('generi')
        # Rimuove le preferenze esistenti per l'utente
        GeneriPreferiti.query.filter_by(utente_id=session['user_id']).delete()
        # Aggiunge i nuovi generi selezionati
        for genere in generi_selezionati:
            nuovo_preferito = GeneriPreferiti(utente_id=session['user_id'], genere=genere)
            db.session.add(nuovo_preferito)
        db.session.commit()
        flash("Preferenze aggiornate con successo!", "success")
        return redirect('/profilo')
    
    # Per la richiesta GET, recupera i generi già selezionati
    preferiti_correnti = [gp.genere for gp in GeneriPreferiti.query.filter_by(utente_id=session['user_id']).all()]

    return render_template(
        'form_preferenze_genere.html',
        generi_disponibili=generi_disponibili,
        generi_selezionati=preferiti_correnti,
        messaggio=None
    )


#--------ATTORI-----------

@app.route('/form_preferenze_attori') 
def form_preferenze_attore():
    return render_template('form_preferenze_attori.html')



@app.route('/ricercaAttore', methods=['GET'])
def ricercaAttore():
    nome_attore_query = request.args.get('nome', '')
    risultati = []

    if nome_attore_query:
        risultati = Attore.query.filter(
            Attore.nome.ilike(f"%{nome_attore_query}%")
        ).all()

    return render_template('form_preferenze_attori.html', risultati=risultati)


@app.route('/aggiungiAttorePreferito', methods=['POST'])
def aggiungi_attore_preferito():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    attore_id = request.form['attore_id']

    # Verifica se l'attore esiste nel database
    attore = Attore.query.get(attore_id)
    if not attore:
        flash('Attore non trovato.', 'danger')
        return redirect(url_for('form_preferenze_attore'))

    # Verifica se l'attore è già nei preferiti dell'utente
    preferito_esistente = AttorePreferito.query.filter_by(utente_id=user_id,attore_id=attore_id).first()

    if not preferito_esistente:
        nuovo_preferito = AttorePreferito(utente_id=user_id, attore_id=attore_id)
        db.session.add(nuovo_preferito)
        db.session.commit()
        flash('Attore aggiunto ai preferiti!', 'success')
    else:
        flash('Attore già nei preferiti!', 'warning')

    return redirect(url_for('profilo'))

@app.route('/rimuoviAttorePreferito', methods=['POST'])
def rimuovi_attore_preferito():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    attore_id = request.form.get('attore_id')

    if not attore_id:
        flash('ID dell\'attore mancante.', 'danger')
        return redirect(url_for('profilo'))

    preferito = AttorePreferito.query.filter_by(utente_id=user_id, attore_id=attore_id).first()

    if preferito:
        db.session.delete(preferito)
        db.session.commit()
        flash('Attore rimosso dai preferiti!', 'success')
    else:
        flash('Attore non trovato nei preferiti.', 'danger')

    return redirect(url_for('profilo'))

#---------------------REGISTI--------------------------
@app.route('/form_preferenze_registi') 
def form_preferenze_regista():
    return render_template('form_preferenze_registi.html')


@app.route('/ricercaRegista', methods=['GET'])
def ricercaRegista():
    nome_regista_query = request.args.get('nome', '')
    risultati = []

    if nome_regista_query:
        risultati = Regista.query.filter(
            Regista.nome.ilike(f"%{nome_regista_query}%")).all()

    return render_template('form_preferenze_registi.html', risultati=risultati)
                    
@app.route('/aggiungiRegistaPreferito', methods=['POST'])
def aggiungi_regista_preferito():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    regista_id = request.form['regista_id']

    # Verifica se l'attore esiste nel database
    regista = Regista.query.get(regista_id)
    if not regista:
        flash('Regista non trovato.', 'danger')
        return redirect(url_for('form_preferenze_regista'))

    # Verifica se l'attore è già nei preferiti dell'utente
    preferito_esistente = RegistaPreferito.query.filter_by(utente_id=user_id,regista_id=regista_id).first()

    if not preferito_esistente:
        nuovo_preferito = RegistaPreferito(utente_id=user_id, regista_id=regista_id)
        db.session.add(nuovo_preferito)
        db.session.commit()
        flash('Regista aggiunto ai preferiti!', 'success')
    else:
        flash('Regista già nei preferiti!', 'warning')

    return redirect('/profilo')


@app.route('/rimuoviRegistaPreferito', methods=['POST'])
def rimuovi_regista_preferito():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    regista_id = request.form.get('regista_id')

    if not regista_id:
        flash('ID del regista mancante.', 'danger')
        return redirect(url_for('profilo'))

    preferito = RegistaPreferito.query.filter_by(utente_id=user_id, regista_id=regista_id).first()

    if preferito:
        db.session.delete(preferito)
        db.session.commit()
        flash('Regista rimosso dai preferiti!', 'success')
    else:
        flash('Regista non trovato nei preferiti.', 'danger')

    return redirect(url_for('profilo'))

#------------------FILM--------------------

@app.route('/form_preferenze_film') 
def form_preferenze_film():
    return render_template('form_preferenze_film.html')

@app.route('/ricercaFilm', methods=['GET'])
def ricercaFilm():
    titolo_query = request.args.get('title', '')
    risultati = []

    if titolo_query:
        risultati = Film.query.filter(
            Film.title.ilike(f"%{titolo_query}%")
        ).all()
        print("sono in ricerca film")
    

    return render_template('form_preferenze_film.html', risultati=risultati)

@app.route('/aggiungiFilmPreferito', methods=['POST'])
def aggiungi_film_preferito():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    movie_id = request.form['film_id']

    # Verifica se il film esiste
    film = Film.query.get(movie_id)
    if not film:
        flash('Film non trovato.', 'danger')
        return redirect(url_for('form_preferenze_film'))

    # Controlla se è già preferito
    preferito_esistente = FilmPreferito.query.filter_by(
        utente_id=user_id,
        movie_id=movie_id
    ).first()

    if not preferito_esistente:
        nuovo_preferito = FilmPreferito(
            utente_id=user_id,
            movie_id=movie_id
        )
        db.session.add(nuovo_preferito)
        db.session.commit()
        flash('Film aggiunto ai preferiti!', 'success')
    else:
        flash('Questo film è già nei preferiti!', 'warning')

    return redirect(url_for('profilo'))


@app.route('/rimuoviFilmPreferito', methods=['POST'])
def rimuovi_film_preferito():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    film_id = request.form.get('film_id')

    if not film_id:
        flash('ID del film mancante.', 'danger')
        return redirect(url_for('profilo'))

    preferito = FilmPreferito.query.filter_by(utente_id=user_id, movie_id=film_id).first()

    if preferito:
        db.session.delete(preferito)
        db.session.commit()
        flash('Film rimosso dai preferiti!', 'success')
    else:
        flash('Film non trovato nei preferiti.', 'danger')

    return redirect(url_for('profilo'))



@app.route('/descrizione/<int:film_id>')
def film_dettagli(film_id):
    if 'user_id' not in session:
        flash('Devi effettuare il login', 'warning')
        return redirect('/login')

    # Recupera i dettagli del film
    film = Film.query.get(film_id)
    if not film:
        flash('Film non trovato', 'danger')
        return redirect('/user')

    # Recupera gli attori, regista e generi associati al film
    attori = film.attori
    regista = film.regista
    generi = film.generi

    return render_template(
        'film_dettagli.html',
        film=film,
        attori=attori,
        regista=regista,
        generi=generi
    )


#-------------------RATINGS--------------------
@app.route('/valuta_film', methods=['GET', 'POST'])
def valuta_film():
    if 'user_id' not in session:
        return redirect('/login')
    
    # Ricerca film
    if request.method == 'GET':
        titolo = request.args.get('title', '')
        risultati = []
        if titolo:
            risultati = Film.query.filter(Film.title.ilike(f"%{titolo}%")).all()
        return render_template('form_valutazione.html', risultati=risultati)
    
    
    # Salva rating
    elif request.method == 'POST':
        user_id = session['user_id']
        movie_id = request.form.get('movie_id')
        rating = request.form.get('rating')
        
        if not rating or not movie_id:
            flash('Seleziona un voto prima di inviare', 'danger')
            return redirect(url_for('valuta_film'))
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            flash('Valutazione non valida', 'danger')
            return redirect(url_for('valuta_film'))
        
        # Verifica esistenza film
        film = Film.query.get(movie_id)
        if not film:
            flash('Film non trovato', 'danger')
            return redirect(url_for('valuta_film'))
        
        # Salva/aggiorna rating
        rating_esistente = RatingUtente.query.filter_by(
            utente_id=user_id,
            movie_id=movie_id
        ).first()

        try:
            if rating_esistente:
                rating_esistente.rating = rating
            else:
                nuovo_rating = RatingUtente(
                    utente_id=user_id,
                    movie_id=movie_id,
                    rating=rating
                )
                db.session.add(nuovo_rating)
            
            db.session.commit()
            flash('Valutazione salvata con successo! ★' * rating, 'success')
            return redirect(url_for('profilo'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Errore durante il salvataggio: {str(e)}", 'danger')
        
        return redirect(url_for('valuta_film'))

@app.route('/rimuoviRating', methods=['POST'])
def rimuovi_rating():
    if 'user_id' not in session:
        flash('Devi effettuare il login', 'danger')
        return redirect('/login')

    user_id = session['user_id']
    film_id = request.form.get('film_id')

    print(f"Tentativo di rimozione - User: {user_id}, Film: {film_id}")  # Debug

    if not film_id:
        flash('ID film mancante', 'danger')
        return redirect(url_for('profilo'))

    try:
        # Converti a intero
        film_id = int(film_id)
        
        # Cerca la valutazione
        rating = RatingUtente.query.filter_by(
            utente_id=user_id,
            movie_id=film_id
        ).first()

        if not rating:
            print("Valutazione non trovata nel DB")  # Debug
            flash('Valutazione non trovata', 'danger')
            return redirect(url_for('profilo'))

        print(f"Trovato rating da eliminare: {rating}")  # Debug
        
        # Eliminazione
        db.session.delete(rating)
        db.session.commit()
        
        print("Valutazione eliminata con successo")  # Debug
        flash('Valutazione rimossa!', 'success')
        
    except ValueError:
        print(f"Errore conversione ID: {film_id}")  # Debug
        flash('ID film non valido', 'danger')
    except Exception as e:
        db.session.rollback()
        print(f"Errore DB: {str(e)}")  # Debug
        flash('Errore durante la rimozione', 'danger')

    return redirect(url_for('profilo'))

#-------------------COMMUNITY--------------------
@app.route("/esegui", methods=["POST"])
def esegui():
    scelta = request.form.get("opzione")
    if scelta == "1":
        return redirect('/user_community')
    elif scelta == "2":
        return redirect('/genres_community')



@app.route('/user_community')
def users_community():
    if 'user_id' not in session:
        flash('Devi effettuare il login', 'warning')
        return redirect('/login')

    # Crea il grafo delle community
    G = crea_community_utenti(db.session)

    # Salva il grafo come immagine
    import matplotlib.pyplot as plt
    pos = nx.spring_layout(G)  # Layout del grafo
    plt.figure(figsize=(10, 8))
    nx.draw(
        G, pos, with_labels=True, node_color='skyblue', edge_color='gray',
        node_size=2000, font_size=10, font_weight='bold'
    )
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.title("Community degli Utenti")
    plt.savefig('static/images/user_community_graph.png')  # Salva l'immagine nella cartella static
    plt.close()  # Chiudi la figura per liberare memoria

    # Renderizza la pagina HTML
    return render_template('user_community.html')


@app.route('/genres_community')
def genres_community():
    if 'user_id' not in session:
        flash('Devi effettuare il login', 'warning')
        return redirect('/login')

    # Genera il grafo dei generi e salva l'immagine in static/images
    genera_immagine_community_generi(
        csv_path="data/movies.csv",
        output_path="static/images/genres_community_graph.png"
    )

    return render_template('genres_community.html')



#--------------NLP SYSTEM---------------
@app.route('/search_description', methods=['POST'])
def search_description():
    descrizione = request.form.get('descrizione')
    if not descrizione:
        return "Descrizione mancante", 400

    Session = sessionmaker(bind=db.engine)
    session_db = Session()
    
    risultati = cerca_film_simili(session_db, descrizione, top_k=50)
    risultati = sorted(risultati, key=lambda x: x[1], reverse=True)

    results = []
    for f, score in risultati:
        generi = ", ".join([g.nome for g in f.generi]) if f.generi else ""
        # Usa descrizione italiana, poi inglese, poi fallback
        descrizione_film = f.descrizione or f.descrizione_eng or "Descrizione mancante"
        results.append({
            'movieId': f.movieId,
            'title': f.title,
            'url': f.url,
            'genres': generi,
            'descrizione': descrizione_film
        })

    return render_template('description_search.html', risultati=results)


@app.route('/search_description_page')
def search_description_page():
    return render_template('description_search.html')


#-------------RACCOMANDAZIONE COLLABORATIVA-------------------


@app.route('/raccomanda', methods=['POST'])
def raccomanda():
    utente_id = request.form.get('utente_id')
    if not utente_id:
        return "utente_id mancante", 400

    try:
        utente_id = int(utente_id)
    except ValueError:
        return "utente_id non valido", 400

    # Crea sessione
    Session = sessionmaker(bind=db.engine)
    session_db = Session()

    # Richiama la funzione di raccomandazione
    try:
        raccomandazioni = raccomanda_film_per_utente(utente_id)
    except Exception as e:
        return f"Errore durante la raccomandazione: {str(e)}", 500

    if not raccomandazioni:
        return "Nessuna raccomandazione trovata", 404

    # Recupera i film dal database
    movie_ids = [movie_id for movie_id, _ in raccomandazioni]
    film_oggetti = session_db.query(Film).filter(Film.movieId.in_(movie_ids)).all()
    film_dict = {film.movieId: film for film in film_oggetti}

    # Prepara risposta
    risultati = []
    for movie_id, score in raccomandazioni:
        film = film_dict.get(movie_id)
        if not film:
            continue

        generi = ", ".join([g.nome for g in film.generi]) if film.generi else ""
        descrizione_film = film.descrizione or film.descrizione_eng or "Descrizione mancante"

        risultati.append({
            'movieId': film.movieId,
            'title': film.title,
            'url': film.url,
            'genres': generi,
            'descrizione': descrizione_film,
            'score': round(score, 3)
        })

    # Ordina per score e limita a 50
    risultati = sorted(risultati, key=lambda x: x['score'], reverse=True)[:50]
    return jsonify(risultati)



@app.route('/raccomanda_user_based', methods=['POST'])
def raccomanda_user_based():
    utente_id = request.form.get('utente_id')
    if not utente_id:
        return "utente_id mancante", 400

    try:
        utente_id = int(utente_id)
    except ValueError:
        return "utente_id non valido", 400

    # Crea sessione
    Session = sessionmaker(bind=db.engine)
    session_db = Session()

    # Richiama la funzione di raccomandazione (user-based)
    try:
        raccomandazioni = raccomanda_film_per_utente_user_based(utente_id)
    except Exception as e:
        return f"Errore durante la raccomandazione: {str(e)}", 500

    if not raccomandazioni:
        return "Nessuna raccomandazione trovata", 404

    # Recupera i film dal database
    movie_ids = [movie_id for movie_id, _ in raccomandazioni]
    film_oggetti = session_db.query(Film).filter(Film.movieId.in_(movie_ids)).all()
    film_dict = {film.movieId: film for film in film_oggetti}

    # Prepara risposta
    risultati = []
    for movie_id, score in raccomandazioni:
        film = film_dict.get(movie_id)
        if not film:
            continue

        generi = ", ".join([g.nome for g in film.generi]) if film.generi else ""
        descrizione_film = film.descrizione or film.descrizione_eng or "Descrizione mancante"

        risultati.append({
            'movieId': film.movieId,
            'title': film.title,
            'url': film.url,
            'genres': generi,
            'descrizione': descrizione_film,
            'score': round(score, 3)
        })

    # Ordina per score e limita a 50
    risultati = sorted(risultati, key=lambda x: x['score'], reverse=True)[:50]
    return jsonify(risultati)





#--------------RACCOMANDAZIONE IBRIDA------------------------------

@app.route('/ibrido', methods=['POST'])
def ibrido():
    utente_id = request.form.get('utente_id')
    if not utente_id:
        return "utente_id mancante", 400

    try:
        utente_id = int(utente_id)
    except ValueError:
        return "utente_id non valido", 400

    # Crea sessione DB esplicita
    Session = sessionmaker(bind=db.engine)
    session_db = Session()

    try:
        # Usa il modello ibrido (puoi regolare alpha e top_n)
        raccomandazioni = raccomanda_film_ibrido(utente_id, session_db, alpha=0.5, top_n=50)
    except Exception as e:
        return f"Errore durante la raccomandazione: {str(e)}", 500

    if not raccomandazioni:
        return "Nessuna raccomandazione trovata", 404

    risultati = []
    for film in raccomandazioni:
        generi = ", ".join([g.nome for g in film.generi]) if film.generi else ""
        descrizione_film = film.descrizione or getattr(film, 'descrizione_eng', None) or "Descrizione mancante"

        risultati.append({
            'movieId': film.movieId,
            'title': getattr(film, 'title', getattr(film, 'titolo', 'Titolo mancante')),
            'url': getattr(film, 'url', None),
            'genres': generi,
            'descrizione': descrizione_film,
            # Nota: qui non hai punteggio, perché il modello ibrido ritorna solo oggetti Film.
            # Se vuoi il punteggio, modifica la funzione ibrida per ritornarlo!
        })

    return jsonify(risultati)



if __name__ == "__main__":
    app.run(debug=True)



