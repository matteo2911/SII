import pandas as pd
import re

# Leggi il file CSV
df = pd.read_csv('data/movies_con_features.csv')

# Estrai l'anno usando una regex più precisa
pattern = r'\((\d{4})\)$'  # Cerca 4 cifre tra parentesi alla fine del titolo
df['anno'] = df['title'].str.extract(pattern, flags=re.IGNORECASE)

# Pulisci il titolo rimuovendo l'anno
df['title'] = df['title'].str.replace(r'\s*\(\d{4}\)$', '', regex=True)

# Converti la colonna anno a intero e gestisci valori mancanti
df['anno'] = pd.to_numeric(df['anno'], errors='coerce').fillna(0).astype(int)

# Controlla i titoli modificati
print(df[['title', 'anno']].head())

# Salva il nuovo CSV
df.to_csv('data/movies.csv', index=False)