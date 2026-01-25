from itertools import combinations
import networkx as nx
import matplotlib.pyplot as plt
from database import AttorePreferito, FilmPreferito, GeneriPreferiti, RegistaPreferito, Utente

def calcola_similarita(utente1, utente2):

    
    # Calcola la somiglianza per attori
    attori1 = {a.attore_id for a in AttorePreferito.query.filter_by(utente_id=utente1.id).all()}
    attori2 = {a.attore_id for a in AttorePreferito.query.filter_by(utente_id=utente2.id).all()}
    sim_attori = len(attori1 & attori2) / len(attori1 | attori2) if attori1 | attori2 else 0

    # Calcola la somiglianza per registi
    registi1 = {r.regista_id for r in RegistaPreferito.query.filter_by(utente_id=utente1.id).all()}
    registi2 = {r.regista_id for r in RegistaPreferito.query.filter_by(utente_id=utente2.id).all()}
    sim_registi = len(registi1 & registi2) / len(registi1 | registi2) if registi1 | registi2 else 0

    # Calcola la somiglianza per generi
    generi1 = {g.genere for g in GeneriPreferiti.query.filter_by(utente_id=utente1.id).all()}
    generi2 = {g.genere for g in GeneriPreferiti.query.filter_by(utente_id=utente2.id).all()}
    sim_generi = len(generi1 & generi2) / len(generi1 | generi2) if generi1 | generi2 else 0

    # Calcola la somiglianza per film
    film1 = {f.movie_id for f in FilmPreferito.query.filter_by(utente_id=utente1.id).all()}
    film2 = {f.movie_id for f in FilmPreferito.query.filter_by(utente_id=utente2.id).all()}
    sim_film = len(film1 & film2) / len(film1 | film2) if film1 | film2 else 0

    # Media pesata delle somiglianze
    somiglianza_totale = (0.3 * sim_attori + 0.3 * sim_registi + 0.2 * sim_generi + 0.2 * sim_film)
    return somiglianza_totale


def crea_community_utenti(db_session, soglia=0.6):

    # Recupera tutti gli utenti
    utenti = db_session.query(Utente).all()

    # Crea un grafo
    G = nx.Graph()

    # Aggiungi nodi (utenti)
    for utente in utenti:
        G.add_node(utente.id, nome=utente.nome, cognome=utente.cognome)

    # Calcola la somiglianza tra ogni coppia di utenti
    for utente1, utente2 in combinations(utenti, 2):
        somiglianza = calcola_similarita(utente1, utente2)
        if somiglianza > soglia:
            G.add_edge(utente1.id, utente2.id, weight=somiglianza)

    return G




def visualizza_grafo(G):

    pos = nx.spring_layout(G)  
    plt.figure(figsize=(10, 8))
    nx.draw(
        G, pos, with_labels=True, node_color='skyblue', edge_color='gray',
        node_size=2000, font_size=10, font_weight='bold'
    )
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.title("Community di Utenti")
    plt.show()