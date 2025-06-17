import pandas as pd

# Carica i file
df_principale = pd.read_csv('data/movies.csv')
df_tag = pd.read_csv('data/tag_uniti.csv')

# Raggruppa i tag per movieId in una singola stringa separata da virgole
df_tag_grouped = df_tag.groupby('movieId')['tag'].apply(lambda tags: ', '.join(tags.astype(str))).reset_index()

# Unisci i file sul campo movieId
df_finale = df_principale.merge(df_tag_grouped, on='movieId', how='left')

# Riempie i NaN (se non ci sono tag) con stringa vuota
df_finale['tag'] = df_finale['tag'].fillna('')

# Salva il nuovo CSV
df_finale.to_csv('data/movies.csv', index=False)
