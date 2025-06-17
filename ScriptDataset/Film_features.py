import pandas as pd
import requests
import time

# Inserisci qui la tua API key di TMDB
API_KEY = 'abde2f685385e5341a0ce493846d787c'
BASE_URL = 'https://api.themoviedb.org/3'

def get_movie_credits(tmdb_id):
    """
    Richiede i credits (cast e crew) del film dato il tmdb_id.
    """
    url = f"{BASE_URL}/movie/{tmdb_id}/credits"
    params = {'api_key': API_KEY, 'language': 'it-IT'}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Errore nei credits per tmdb_id {tmdb_id} (status code {response.status_code})")
        return None

def get_movie_details(tmdb_id):
    """
    Richiede i dettagli del film (in particolare la popolarità e la descrizione) dato il tmdb_id.
    """
    url = f"{BASE_URL}/movie/{tmdb_id}"
    params = {'api_key': API_KEY, 'language': 'it-IT'}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Errore nei dettagli per tmdb_id {tmdb_id} (status code {response.status_code})")
        return None

def process_movie(tmdb_id):
    """
    Per il film identificato da tmdb_id, estrae:
      - I primi 5 attori (dalla lista cast)
      - Il regista (cercando il membro con job "Director" nel crew)
      - La popolarità (dal dettaglio del film)
      - La descrizione (overview) del film
    """
    credits = get_movie_credits(tmdb_id)
    details = get_movie_details(tmdb_id)
    
    # Estrai gli attori: prendi i primi 5 elementi della lista cast
    attori = []
    if credits and "cast" in credits:
        cast = credits.get('cast', [])
        for c in cast[:5]:
            name = c.get('name')
            if name:
                attori.append(name)
    attori_str = ', '.join(attori)

    # Estrai il regista (job "Director")
    regista = ""
    if credits and "crew" in credits:
        crew = credits.get('crew', [])
        for member in crew:
            if member.get('job') == "Director":
                regista = member.get('name', "")
                break

    # Estrai la popolarità e la descrizione dal dettaglio del film
    popolarita = None
    descrizione = ""
    if details:
        popolarita = details.get('popularity')
        descrizione = details.get('overview', "")
    
    return attori_str, regista, popolarita, descrizione

def main():
    # Carica il file CSV originale
    df = pd.read_csv('data/movies_con_tmdbId_e_rating.csv')
    
    # Prepara le liste per i nuovi campi
    attori_list = []
    regista_list = []
    popolarita_list = []
    descrizione_list = []

    # Itera per ogni film del DataFrame
    for idx, row in df.iterrows():
        tmdb_id = row['tmdbId']
        title = row.get('title', 'No Title')
        print(f"Elaboro film tmdbId {tmdb_id} - {title}...")
        
        # Ottieni i dati dal TMDB per il film corrente
        attori, regista, popolarita, descrizione = process_movie(tmdb_id)
        
        # Verifica che tutti i campi siano stati caricati correttamente
        if attori and regista and (popolarita is not None) and descrizione:
            print(f"Film {tmdb_id} - {title}: Caricamento OK")
        else:
            # Se la descrizione non è stata caricata, imposta "NULL"
            if not descrizione:
                descrizione = "NULL"
            print(f"Film {tmdb_id} - {title}: Caricamento FALLITO")

        # Aggiungi i risultati alle liste
        attori_list.append(attori)
        regista_list.append(regista)
        popolarita_list.append(popolarita)
        descrizione_list.append(descrizione)
        
        # Ogni 300 film, salva un CSV parziale con i dati finora raccolti
        if (idx + 1) % 300 == 0:
            df.loc[:idx, 'attori'] = attori_list
            df.loc[:idx, 'regista'] = regista_list
            df.loc[:idx, 'popolarita'] = popolarita_list
            df.loc[:idx, 'descrizione'] = descrizione_list
            partial_file = f"movies_con_info_tmdb_partial_{idx + 1}.csv"
            df.head(idx + 1).to_csv(partial_file, index=False)
            print(f"Salvato file parziale: {partial_file}")
        
        # Una breve pausa per non sovraccaricare l'API
        time.sleep(0.25)

    # Alla fine, aggiungi tutte le nuove colonne al DataFrame
    df['attori'] = attori_list
    df['regista'] = regista_list
    df['popolarita'] = popolarita_list
    df['descrizione'] = descrizione_list

    # Salva il DataFrame aggiornato in un nuovo file CSV finale
    output_file = 'data/movies_con_info_tmdb.csv'
    df.to_csv(output_file, index=False)
    print(f"File aggiornato salvato come '{output_file}'")

if __name__ == "__main__":
    main()
