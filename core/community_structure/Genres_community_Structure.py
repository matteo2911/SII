import itertools
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import os
import community.community_louvain as community_louvain

CSV_FILE = "data/movies.csv"

def carica_dati_csv(file_csv):
    df = pd.read_csv(file_csv)
    film_categorie = []
    for genres in df["genres"].astype(str):
        cats = [g for g in genres.split("|") if g and g != "(no genres listed)"]
        if cats:
            film_categorie.append(cats)
    return film_categorie

def crea_grafo_jaccard(film_categorie):
    
    genre_count = {}
    cooc = {}

    for cats in film_categorie:
        cats = list(dict.fromkeys(cats))  # unique, preserve order
        for g in cats:
            genre_count[g] = genre_count.get(g, 0) + 1
        for a, b in itertools.combinations(sorted(cats), 2):
            cooc[(a, b)] = cooc.get((a, b), 0) + 1

    
    G = nx.Graph()
    for (a, b), c in cooc.items():
        w = c / (genre_count[a] + genre_count[b] - c)
        G.add_edge(a, b, weight=w, cooc=c)

    return G, genre_count

def rileva_comunita(G):
    
    return community_louvain.best_partition(G, weight="weight", random_state=42, resolution=1.0)

def salva_grafo(G, partition, genre_count, filepath="static/images/genres_community_graph.png"):
    
    colori = ["skyblue", "green", "yellow", "orange", "purple", "pink", "red", "brown", "gray", "cyan"]


    
    pos = nx.spring_layout(G, seed=42)

    plt.figure(figsize=(12, 12))

    
    comunità = sorted(set(partition.values()))
    for i, com in enumerate(comunità):
        nodes = [n for n in partition if partition[n] == com]
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=nodes,
            node_size=1400,
            node_color=[colori[i % len(colori)]] * len(nodes)
        )

    # --- ARCHI: tieni solo i più forti ---
    TOP_K_PER_NODE = 4  

    keep = set()
    for n in G.nodes():
        # prendo i vicini ordinati per peso (Jaccard) decrescente
        vicini = sorted(G[n].items(), key=lambda x: x[1].get("weight", 0), reverse=True)[:TOP_K_PER_NODE]
        for nb, _attr in vicini:
            keep.add(tuple(sorted((n, nb))))

    edgelist = list(keep)

    nx.draw_networkx_edges(G, pos, edgelist=edgelist, alpha=0.5)

    # etichette 
    nx.draw_networkx_labels(G, pos, font_size=12)

    plt.title("Rete delle categorie dei film con le comunità", size=15)
    plt.axis("off")
    plt.savefig(filepath, bbox_inches="tight")
    plt.close()


def genera_immagine_community_generi(
    csv_path=CSV_FILE,
    output_path="static/images/genres_community_graph.png"
):
    film_categorie = carica_dati_csv(csv_path)
    G, genre_count = crea_grafo_jaccard(film_categorie)
    partition = rileva_comunita(G)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    salva_grafo(G, partition, genre_count, filepath=output_path)

    return output_path