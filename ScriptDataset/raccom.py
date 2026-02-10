# Step 0: Importa librerie necessarie
import pandas as pd
import json
from scipy.sparse import csr_matrix, save_npz
from sklearn.metrics.pairwise import cosine_similarity

# Step 1: Carica il dataset dei rating
ratings = pd.read_csv('data/No_Used/rating.csv')
print(f"Totale rating caricati: {ratings.shape[0]}")

# Step 2: Filtra solo i rating >= 4
ratings = ratings[ratings['rating'] >= 4]
print(f"Dopo filtro rating >= 4: {ratings.shape[0]} rating")

# Step 3: Filtra utenti con almeno 100 rating
user_counts = ratings['userId'].value_counts()
valid_users = user_counts[user_counts >= 100].index
ratings = ratings[ratings['userId'].isin(valid_users)]
print(f"Dopo filtro utenti: {ratings.shape[0]} rating, {len(valid_users)} utenti")

# Step 4: Filtra film con almeno 25 rating
movie_counts = ratings['movieId'].value_counts()
valid_movies = movie_counts[movie_counts >= 25].index
ratings = ratings[ratings['movieId'].isin(valid_movies)]
print(f"Dopo filtro film: {ratings.shape[0]} rating, {len(valid_movies)} film")

# Step 5: Crea matrice user-item con veri movieId
user_item_matrix = ratings.pivot(
    index='userId',
    columns='movieId',
    values='rating'
).fillna(0)
print(f"Matrice user-item: {user_item_matrix.shape} (utenti x film)")

# Step 6: Converti in matrice sparsa
sparse_matrix = csr_matrix(user_item_matrix.values)

# Step 7: Calcola similarità cosine tra film (trasposta)
similarity_matrix = cosine_similarity(sparse_matrix.T)
similarity_matrix[similarity_matrix < 0.1] = 0  # ⛔ Filtra le similarità troppo basse

# Step 8: Converte in matrice sparsa
sparse_similarity_matrix = csr_matrix(similarity_matrix)

# Step 9: Salva la matrice sparsa
save_npz("similarity_matrix_sparse.npz", sparse_similarity_matrix)
print(" Matrice di similarità sparsa salvata in 'similarity_matrix_sparse.npz'")

# Step 10: Salva i mapping movieId <-> indice
movie_ids = list(user_item_matrix.columns)  # veri movieId

id_to_index = {str(mid): i for i, mid in enumerate(movie_ids)}
index_to_id = {i: int(mid) for i, mid in enumerate(movie_ids)}

with open('id_to_index.json', 'w') as f:
    json.dump(id_to_index, f)
with open('index_to_id.json', 'w') as f:
    json.dump(index_to_id, f)

print(" Mapping ID salvati in 'id_to_index.json' e 'index_to_id.json'")
