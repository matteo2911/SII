import pandas as pd
import requests
import time
import csv

API_KEY = "abde2f685385e5341a0ce493846d787c"  # Inserisci qui la tua TMDB API Key
INPUT_CSV = "data/movies_con_tmdbId_e_rating.csv"
OUTPUT_CSV = "film_features_restanti_output.csv"

def get_film_info(tmdb_id):
    base_url = "https://api.themoviedb.org/3/movie/"
    credits_url = f"{base_url}{tmdb_id}/credits?api_key={API_KEY}"
    details_url = f"{base_url}{tmdb_id}?api_key={API_KEY}"

    try:
        # Credits
        credits_response = requests.get(credits_url)
        credits_data = credits_response.json()

        # Prendi i primi 5 attori
        cast = credits_data.get('cast', [])
        attori = [person['name'] for person in cast[:5]]
        if len(attori) < 5:
            attori += [""] * (5 - len(attori))

        # Trova il regista
        crew = credits_data.get('crew', [])
        regista = next((person['name'] for person in crew if person['job'] == 'Director'), "")

        # Dettagli
        details_response = requests.get(details_url)
        details_data = details_response.json()

        popolarita = details_data.get('popularity', None)
        descrizione = details_data.get('overview', None)

        if descrizione is None:
            descrizione = "NULL"
            stato = "FALLITO"
        elif None in [attori, regista, popolarita]:
            stato = "FALLITO"
        else:
            stato = "OK"

        return attori, regista, popolarita, descrizione, stato

    except Exception:
        return [""] * 5, "", None, "NULL", "FALLITO"

def process_movies():
    df = pd.read_csv(INPUT_CSV)
    output_data = []

    start_index = df[df['movieId'] == 117576].index[0] + 1

    for i in range(start_index, len(df)):
        row = df.iloc[i]
        movie_id = row['movieId']
        title = row['title']
        genres = row['genres']
        tmdb_id = row['tmdbId']
        numero_voti = row['numero_voti']
        media_voti = row['media_voti']

        attori, regista, popolarita, descrizione, stato = get_film_info(tmdb_id)

        output_data.append([
            movie_id, title, genres, tmdb_id, numero_voti, media_voti,
            ", ".join(attori), regista, popolarita, descrizione
        ])

        # Stampa compatibile con Windows (senza emoji o unicode)
        print(f"{i}. {title} ({tmdb_id}) - {'OK' if stato == 'OK' else 'FALLITO'}")

        time.sleep(0.25)

    # Salva l'intero risultato in un unico file CSV
    with open(OUTPUT_CSV, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "movieId", "title", "genres", "tmdbId", "numero_voti", "media_voti",
            "attori", "regista", "popolarita", "descrizione"
        ])
        writer.writerows(output_data)

    print("\n✅ Caricamento completato. Dati salvati in:", OUTPUT_CSV)

if __name__ == "__main__":
    process_movies()
