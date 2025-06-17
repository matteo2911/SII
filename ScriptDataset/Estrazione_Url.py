import pandas as pd
import requests
import time
import logging

# Configurazione
API_KEY = 'abde2f685385e5341a0ce493846d787c'
BASE_URL = 'https://api.themoviedb.org/3'
IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/original'  # o 'w500' per dimensioni diverse

# Setup logging
logging.basicConfig(filename='poster_fetch.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_movie_poster(tmdb_id):
    """Recupera l'URL del poster da TMDB con controlli robusti"""
    if pd.isna(tmdb_id):
        logging.warning(f"ID TMDB mancante per film {id}")
        return None
    
    try:
        tmdb_id = int(float(tmdb_id))  # Gestisce casi di numeri come stringhe
    except (ValueError, TypeError):
        logging.warning(f"ID TMDB non valido: {tmdb_id}")
        return None

    url = f"{BASE_URL}/movie/{tmdb_id}"
    params = {
        'api_key': API_KEY,
        'language': 'it-IT'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logging.debug(f"Risposta API per {tmdb_id}: {data}")
        
        if 'poster_path' not in data or not data['poster_path']:
            logging.info(f"Nessun poster trovato per {tmdb_id}")
            return None
            
        poster_url = f"{IMAGE_BASE_URL}{data['poster_path']}"
        logging.info(f"Trovato poster per {tmdb_id}: {poster_url}")
        return poster_url

    except requests.exceptions.RequestException as e:
        logging.error(f"Errore API per {tmdb_id}: {str(e)}")
        return None

def main():
    # Carica i dati
    try:
        df = pd.read_csv('data/movies.csv')
        logging.info(f"Caricato file con {len(df)} righe")
    except Exception as e:
        logging.error(f"Errore caricamento file: {str(e)}")
        return

    # Inizializza colonna poster_url
    df['poster_url'] = None
    success_count = 0

    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"Elaborazione: {idx}/{len(df)} righe")
            logging.info(f"Progresso: {idx}/{len(df)}")

        tmdb_id = row['tmdbId']
        poster_url = get_movie_poster(tmdb_id)

        if poster_url:
            df.at[idx, 'poster_url'] = poster_url
            success_count += 1

        # Salva progressi ogni 300 righe
        if (idx + 1) % 300 == 0:
            backup_file = f"backup_poster_{idx+1}.csv"
            df.to_csv(backup_file, index=False)
            logging.info(f"Salvato backup: {backup_file}")

        time.sleep(0.3)  # Rispetta i limiti di rate

    # Salva risultati finali
    final_file = 'movies_con_poster_final.csv'
    df.to_csv(final_file, index=False)
    
    # Statistiche
    stats = {
        'total_movies': len(df),
        'success_count': success_count,
        'success_rate': (success_count/len(df))*100,
        'missing_ids': df['tmdbId'].isna().sum(),
        'empty_posters': df['poster_url'].isna().sum()
    }
    
    print("\n=== Statistiche ===")
    print(f"Film totali: {stats['total_movies']}")
    print(f"Poster trovati: {stats['success_count']}")
    print(f"Percentuale successo: {stats['success_rate']:.2f}%")
    print(f"ID TMDB mancanti: {stats['missing_ids']}")
    print(f"Poster mancanti: {stats['empty_posters']}")
    
    logging.info("Elaborazione completata")
    logging.info(f"Statistiche: {stats}")

if __name__ == "__main__":
    main()