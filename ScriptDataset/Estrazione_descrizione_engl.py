import pandas as pd
import requests
import time

API_KEY = 'abde2f685385e5341a0ce493846d787c'
BASE_URL = 'https://api.themoviedb.org/3'

def get_english_description(tmdb_id):
    """
    Ottiene la descrizione (overview) in inglese per un dato film TMDB.
    """
    url = f"{BASE_URL}/movie/{tmdb_id}"
    params = {'api_key': API_KEY, 'language': 'en-US'}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('overview', '')
    else:
        print(f"Errore per tmdb_id {tmdb_id} (status {response.status_code})")
        return ''

def main():
    df = pd.read_csv('data/movies.csv')
    
    descrizioni_en = []

    for idx, row in df.iterrows():
        tmdb_id = row['tmdbId']
        title = row.get('title', 'N/A')
        print(f"[{idx+1}/{len(df)}] Elaboro: {title} (tmdbId={tmdb_id})")
        
        descrizione = get_english_description(tmdb_id)
        if not descrizione:
            descrizione = "NULL"
            print(" -> Descrizione mancante")
        else:
            print(" -> OK")
        
        descrizioni_en.append(descrizione)

        # Salva ogni 300 film per sicurezza
        if (idx + 1) % 300 == 0:
            df.loc[:idx, 'descrizione_en'] = descrizioni_en
            partial_file = f"data/movies_descrizione_en_partial_{idx + 1}.csv"
            df.head(idx + 1).to_csv(partial_file, index=False)
            print(f" Salvato: {partial_file}")

        time.sleep(0.25)  # evita rate limit

    df['descrizione_en'] = descrizioni_en
    output_file = 'data/movies_con_descrizione_en.csv'
    df.to_csv(output_file, index=False)
    print(f"\n File completo salvato come: {output_file}")

if __name__ == "__main__":
    main()
