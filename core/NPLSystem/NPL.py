import numpy as np
from sentence_transformers import SentenceTransformer, util

from database import Film

# Carica il modello una sola volta
model = SentenceTransformer('all-mpnet-base-v2')

def get_embedding(text):
    return model.encode(text, convert_to_numpy=True).astype(np.float32)

def cerca_film_simili(session, descrizione_input, top_k=50):
    # Embedding della query
    query_embedding = get_embedding(descrizione_input).reshape(1, -1)

    # Recupera film con embedding
    films = session.query(Film).filter(Film.embedding != None).all()

    embeddings = []
    film_list = []

    for film in films:
        if film.embedding:
            emb = np.array(film.embedding, dtype=np.float32)  
            embeddings.append(emb)
            film_list.append(film)

    embeddings = np.array(embeddings, dtype=np.float32)

    # Similarità coseno
    similarita = util.cos_sim(query_embedding, embeddings)[0].cpu().numpy()

    # Ordina per similarità
    top_indices = similarita.argsort()[::-1][:top_k]

    top_films = [(film_list[i], similarita[i]) for i in top_indices]

    return top_films
