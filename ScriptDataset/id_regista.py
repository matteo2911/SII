import csv

file_path = 'data/registi.csv'

# Leggi i dati esistenti
with open(file_path, 'r', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    registi = list(reader)

# Aggiungi colonna attore_id
for idx, attore in enumerate(registi, start=1):
    attore['regista_id'] = idx

# Rinomina le colonne: attore_id prima, poi il resto
fieldnames = ['regista_id'] + [col for col in registi[0] if col != 'regista_id']

# Sovrascrivi il file originale con i nuovi dati
with open(file_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(registi)

print(f"✅ File '{file_path}' aggiornato correttamente con colonna 'regista_id'.")
