import csv

CSV_FILE = 'data/movies_con_tmdbId_e_rating.csv'  

def cerca_film_per_titolo(titolo_da_cercare):
    risultati = []

    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                if titolo_da_cercare.lower() in row['title'].lower():
                    risultati.append({
                        'movieId': row['movieId'],
                        'title': row['title'],
                        'genres': row['genres'],
                        'tmdbId': row.get('tmdbId', 'N/A'),
                        'average_rating': row['media_voti'],
                        'num_ratings': row['numero_voti']
                    })
    except FileNotFoundError:
        print(f"Il file {CSV_FILE} non è stato trovato.")

    return risultati


def cerca_film_per_titolo_form(titolo_da_cercare):
    risultati = []

    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                if titolo_da_cercare.lower() in row['title'].lower():
                    risultati.append({
                        
                        'title': row['title'],
                    
                    })
    except FileNotFoundError:
        print(f" Il file {CSV_FILE} non è stato trovato.")

    return risultati