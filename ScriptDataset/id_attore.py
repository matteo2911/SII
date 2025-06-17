import csv

file_path = 'data/attori.csv'

# Leggi i dati esistenti
with open(file_path, 'r', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    attori = list(reader)

# Aggiungi colonna attore_id
for idx, attore in enumerate(attori, start=1):
    attore['attore_id'] = idx

# Rinomina le colonne: attore_id prima, poi il resto
fieldnames = ['attore_id'] + [col for col in attori[0] if col != 'attore_id']

# Sovrascrivi il file originale con i nuovi dati
with open(file_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(attori)

print(f"✅ File '{file_path}' aggiornato correttamente con colonna 'attore_id'.")
