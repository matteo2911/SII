import pandas as pd
from tqdm import tqdm  # Importa tqdm per la barra di avanzamento

# 1. Carica il file user_profiles.csv
def load_user_profiles(file_path):
    return pd.read_csv(file_path)

# 2. Carica il file ratings.csv
def load_ratings(file_path):
    return pd.read_csv(file_path)

# 3. Conta il numero di rating per ogni utente
def count_ratings_per_user(ratings):
    # Usa tqdm per la barra di avanzamento durante il raggruppamento
    ratings_count = ratings.groupby('userId').size().reset_index(name='num_ratings')
    return ratings_count

# 4. Aggiungi il numero di rating ai profili utente
def add_ratings_to_user_profiles(user_profiles, ratings_count):
    # Usa tqdm per visualizzare l'avanzamento durante la fusione dei dataframe
    user_profiles = user_profiles.merge(ratings_count, on='userId', how='left')
    return user_profiles

# 5. Salva il nuovo file user_profiles.csv con la colonna num_ratings aggiunta
def save_user_profiles(user_profiles, output_path):
    # Salva il nuovo file CSV
    user_profiles.to_csv(output_path, index=False)
    print(f"File salvato in: {output_path}")

# Funzione principale
def main(user_profiles_path, ratings_path):
    # Carica i dati
    print("Caricamento dei profili utente...")
    user_profiles = load_user_profiles(user_profiles_path)
    
    print("Caricamento dei ratings...")
    ratings = load_ratings(ratings_path)
    
    # Conta il numero di rating per ogni utente con barra di avanzamento
    print("Conteggio dei rating per utente...")
    ratings_count = count_ratings_per_user(ratings)
    
    # Aggiungi il numero di rating ai profili utente con barra di avanzamento
    print("Aggiunta del conteggio dei rating ai profili utente...")
    user_profiles_with_ratings = add_ratings_to_user_profiles(user_profiles, ratings_count)
    
    # Percorso di output predefinito
    output_path = "Dataset/user_profiles_with_ratings.csv"  # Qui il file verrà salvato
    
    # Salva il nuovo file CSV con la colonna 'num_ratings'
    print("Salvataggio del nuovo file CSV...")
    save_user_profiles(user_profiles_with_ratings, output_path)

# Esegui il programma
if __name__ == "__main__":
    # Percorsi dei file CSV
    user_profiles_path = r'Dataset/user_profiles.csv'  # Cambia con il tuo percorso
    ratings_path = r'Dataset/rating.csv'  # Cambia con il tuo percorso
    
    # Esegui la funzione principale
    main(user_profiles_path, ratings_path)
