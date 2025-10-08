# app.py
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import networkx as nx
import random

# ----------------------------
# Config
# ----------------------------
EDGE_CSV = "youtube_edges.csv"  # put your CSV in same folder
SAMPLE_SIZE = 200               # sample for closeness centrality
TOP_N = 10                      # top nodes for charts
# ----------------------------

# Create FastAPI app
app = FastAPI(title="YouTube Centrality API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load graph
df_edges = pd.read_csv(EDGE_CSV)
G = nx.from_pandas_edgelist(df_edges, 'source', 'target')

# Compute centrality
deg_cent_all = nx.degree_centrality(G)
bet_cent_all = nx.betweenness_centrality(G, k=TOP_N, seed=42)

# Sample nodes for closeness
nodes_sample = random.sample(list(G.nodes()), min(len(G.nodes()), SAMPLE_SIZE))
clo_cent_sample = {node: nx.closeness_centrality(G, u=node) for node in nodes_sample}

# Combine centrality for all nodes in sample
centrality_df = pd.DataFrame({
    "Node": nodes_sample,
    "Degree": [deg_cent_all.get(node, 0) for node in nodes_sample],
    "Betweenness": [bet_cent_all.get(node, 0) for node in nodes_sample],
    "Closeness": [clo_cent_sample.get(node, 0) for node in nodes_sample],
})

centrality_df_sorted = centrality_df.sort_values(by="Degree", ascending=False)


# ----------------------------
# API Endpoints
# ----------------------------

@app.get("/degree/")
def degree_centrality():
    data = [{"node": n, "value": v} for n, v in deg_cent_all.items()]
    return data

@app.get("/betweenness/")
def betweenness_centrality():
    data = [{"node": n, "value": v} for n, v in bet_cent_all.items()]
    return data

@app.get("/closeness/")
def closeness_centrality():
    data = [{"node": n, "value": clo_cent_sample.get(n, 0)} for n in nodes_sample]
    return data

@app.get("/plot/grouped-bar/")
def grouped_bar_data():
    top_df = centrality_df_sorted.head(TOP_N)
    return top_df.to_dict(orient="records")

@app.get("/plot/centrality-top10/")
def top10_centrality():
    top_df = centrality_df_sorted.head(TOP_N)
    return top_df.to_dict(orient="records")

@app.get("/plot/network-nodes/")
def network_nodes():
    top_nodes = centrality_df_sorted['Node'].head(TOP_N).tolist()
    nodes_to_plot = set(top_nodes)
    for node in top_nodes:
        nodes_to_plot.update(G.neighbors(node))
    subgraph = G.subgraph(nodes_to_plot)
    pos = nx.spring_layout(subgraph, seed=42)

    nodes_data = []
    for node in subgraph.nodes():
        nodes_data.append({
            "node": node,
            "x": pos[node][0],
            "y": pos[node][1],
            "degree": deg_cent_all.get(node, 0),
            "betweenness": bet_cent_all.get(node, 0),
            "closeness": clo_cent_sample.get(node, 0)
        })
    return nodes_data

@app.get("/plot/network-edges/")
def network_edges():
    top_nodes = centrality_df_sorted['Node'].head(TOP_N).tolist()
    nodes_to_plot = set(top_nodes)
    for node in top_nodes:
        nodes_to_plot.update(G.neighbors(node))
    subgraph = G.subgraph(nodes_to_plot)

    edges = [{"source": u, "target": v} for u, v in subgraph.edges()]
    return edges
