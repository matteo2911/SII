import networkx as nx
import matplotlib.pyplot as plt
import community as community_louvain  
import pandas as pd

# Carica  file CSV 
CSV_FILE = 'data/movies.csv'  

# Funzione per caricare il CSV e ottenere le categorie
def carica_dati_csv(file_csv):
    # Carica il CSV in un DataFrame
    df = pd.read_csv(file_csv)
    
    # RestituiscE una lista di film e le loro categorie
    film_categorie = []
    for _, row in df.iterrows():
        categories = row['genres'].split('|')  
        film_categorie.append(categories)
    return film_categorie

# Funzione per creare il grafo delle categorie
def crea_grafo(film_categorie):
    G = nx.Graph()

    # Aggiungi gli archi tra le categorie di ogni film
    for categories in film_categorie:
        for i in range(len(categories)):
            for j in range(i + 1, len(categories)):
                # Se due categorie co-occorrono nello stesso film, aggiungiamo un arco
                if G.has_edge(categories[i], categories[j]):
                    G[categories[i]][categories[j]]['weight'] += 1  # Aumentiamo il peso
                else:
                    G.add_edge(categories[i], categories[j], weight=1)  # Aggiungiamo un arco con peso 1
    
    return G

# Funzione per rilevare le comunità con l'algoritmo Louvain
def rileva_comunita(G):
    # algoritmo di Louvain per rilevare le comunità
    partition = community_louvain.best_partition(G)  
    return partition

# Funzione per salvare il grafo come immagine
def salva_grafo(G, partition, filepath='static/images/genres_community_graph.png'):

  
    colori = ['yellow', 'skyblue', 'green']
    comunità = set(partition.values())
    
    pos = nx.spring_layout(G)  
    plt.figure(figsize=(12, 12))
    
    
    for i, com in enumerate(comunità):
        nodes = [node for node in partition if partition[node] == com]
        nx.draw_networkx_nodes(
            G, pos, nodes, node_size=1400, node_color=[colori[i % len(colori)]] * len(nodes)  # Pallini più grandi
        )
    
    nx.draw_networkx_edges(G, pos, alpha=0.5)
    nx.draw_networkx_labels(G, pos, font_size=12)
    
    plt.title("Rete delle categorie dei film con le comunità", size=15)
    plt.axis('off')
    plt.savefig(filepath)  
    plt.close()  

# Main
def main():
    film_categorie = carica_dati_csv(CSV_FILE)
    G = crea_grafo(film_categorie)
    partition = rileva_comunita(G)
    salva_grafo(G, partition)  

if __name__ == '__main__':
    main()