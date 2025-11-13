import csv


CSV_FILE = 'data/attori.csv'  

def cerca_attore(attore_da_cercare):
    risultati = []

    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
        
                if attore_da_cercare.lower() in row['Nome Attore'].lower():
                    risultati.append({
                        'Nome': row['Nome Attore']
                    })

    except FileNotFoundError:
        print(f" Il file {CSV_FILE} non è stato trovato.")
    
    return risultati
