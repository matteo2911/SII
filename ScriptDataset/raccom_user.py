import sys
print(sys.executable)
print(sys.version)

import pandas as pd
import json
import numpy as np
from scipy.sparse import csr_matrix, save_npz
from sklearn.metrics.pairwise import cosine_similarity
import os

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Step 1: Carica il dataset dei rating
ratings = pd.read_csv(f'{DATA_DIR}/No_Used/rating.csv')
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

# Step 5: Matrice user-item (utenti x film)
user_item_matrix = ratings.pivot(index='userId', columns='movieId', values='rating').fillna(0)
print(f"Matrice user-item: {user_item_matrix.shape} (utenti x film)")

# Step 6: Sparsa
sparse_matrix = csr_matrix(user_item_matrix.values)

# Step 6b: salva anche la matrice user-item (sparsa) per il runtime user-based
save_npz(f"{DATA_DIR}/user_item_matrix_sparse.npz", sparse_matrix)
print("Matrice user-item sparsa salvata in 'data/user_item_matrix_sparse.npz'")

# Step 6c: mapping movieId <-> indice (colonne) per allineare i film
movie_ids = list(user_item_matrix.columns)
movie_id_to_index = {str(mid): i for i, mid in enumerate(movie_ids)}
movie_index_to_id = {i: int(mid) for i, mid in enumerate(movie_ids)}

with open(f"{DATA_DIR}/movie_id_to_index.json", "w") as f:
    json.dump(movie_id_to_index, f)
with open(f"{DATA_DIR}/movie_index_to_id.json", "w") as f:
    json.dump(movie_index_to_id, f)

print("Mapping film salvati in 'data/movie_id_to_index.json' e 'data/movie_index_to_id.json'")

# Step 6d: norme utenti (servono per cosine veloce tra utente DB e utenti CSV)
user_norms = np.sqrt(sparse_matrix.multiply(sparse_matrix).sum(axis=1)).A1
np.save(f"{DATA_DIR}/user_norms.npy", user_norms)
print("Norme utenti salvate in 'data/user_norms.npy'")

# Step 7: Similarità UTENTE-UTENTE (NO .T)
user_similarity = cosine_similarity(sparse_matrix)
user_similarity[user_similarity < 0.1] = 0

# Step 8: Sparsa + salva in data/
save_npz(f"{DATA_DIR}/user_similarity_matrix_sparse.npz", csr_matrix(user_similarity))
print("Matrice user-user salvata in 'data/user_similarity_matrix_sparse.npz'")

# Step 9: mapping userId <-> indice (righe) in data/
user_ids = list(user_item_matrix.index)
user_id_to_index = {str(uid): i for i, uid in enumerate(user_ids)}
user_index_to_id = {i: int(uid) for i, uid in enumerate(user_ids)}

with open(f'{DATA_DIR}/user_id_to_index.json', 'w') as f:
    json.dump(user_id_to_index, f)
with open(f'{DATA_DIR}/user_index_to_id.json', 'w') as f:
    json.dump(user_index_to_id, f)

print("Mapping utenti salvati in 'data/user_id_to_index.json' e 'data/user_index_to_id.json'")
