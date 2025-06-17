import csv

# Insiemi per evitare duplicati
attori_scritti = set()
registi_scritti = set()

# Apri il file CSV originale
with open('data/movies_con_features.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    # Apri i file di output
    with open('data/attori.csv', mode='w', newline='', encoding='utf-8') as attori_file, \
         open('data/registi.csv', mode='w', newline='', encoding='utf-8') as registi_file:
        
        attori_writer = csv.writer(attori_file)
        registi_writer = csv.writer(registi_file)

        # Scrivi intestazioni
        attori_writer.writerow(['Nome Attore'])
        registi_writer.writerow(['Nome Regista'])

        # Itera sulle righe del file film
        for row in reader:
            # ATTORI (separati da virgole!)
            if row['attori']:
                attori_lista = row['attori'].split(',')
                for attore in attori_lista:
                    attore_pulito = attore.strip()
                    if attore_pulito and attore_pulito not in attori_scritti:
                        attori_writer.writerow([attore_pulito])
                        attori_scritti.add(attore_pulito)

            # REGISTI
            if row['regista']:
                regista_pulito = row['regista'].strip()
                if regista_pulito and regista_pulito not in registi_scritti:
                    registi_writer.writerow([regista_pulito])
                    registi_scritti.add(regista_pulito)
