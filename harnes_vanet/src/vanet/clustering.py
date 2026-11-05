"""Clustering primitives: betweenness centrality (paper Eq. 3), greedy cluster
formation (paper Eq. 4, 1-hop clusters), and our composite stability score."""
import networkx as nx
import numpy as np


def bc_scores(nodes, adj, S, lam):
    """Betweenness centrality on the sub-graph induced by `nodes`.
    Edge weight = 1 + lam * (-ln S): unreliable links are 'longer', so BC is
    computed on reliability-weighted shortest paths (paper Eq. 3, which leaves
    the weighting undefined). Returns array aligned with `nodes`."""
    nodes = np.asarray(nodes, dtype=int)
    n = len(nodes)
    out = np.zeros(n)
    if n < 3:
        return out
    sub = adj[np.ix_(nodes, nodes)]
    Ssub = S[np.ix_(nodes, nodes)]
    ii, jj = np.where(np.triu(sub, 1))
    G = nx.Graph()
    G.add_nodes_from(range(n))
    if len(ii):
        w = 1.0 + lam * (-np.log(np.clip(Ssub[ii, jj], 1e-6, 1.0)))
        G.add_weighted_edges_from(zip(ii.tolist(), jj.tolist(), w.tolist()))
    bc = nx.betweenness_centrality(G, weight="weight", normalized=True)
    for k, v in bc.items():
        out[k] = v
    return out


def greedy_form(nodes, score, join_adj):
    """Highest score becomes CH and absorbs all unassigned neighbours it can
    reliably reach. Returns dict vehicle -> head for assigned vehicles only."""
    nodes = np.asarray(nodes, dtype=int)
    inset = set(nodes.tolist())
    order = sorted(range(len(nodes)), key=lambda k: (-score[k], nodes[k]))
    assigned = {}
    for k in order:
        v = int(nodes[k])
        if v in assigned:
            continue
        nb = [int(u) for u in np.where(join_adj[v])[0]
              if int(u) in inset and int(u) not in assigned]
        if not nb:
            continue
        assigned[v] = v
        for u in nb:
            assigned[u] = v
    return assigned


def composite_scores(nodes, nbr_mask, S, L, bc_norm, weights, l_max):
    """Our stability-aware score for each node in `nodes`, computed against the
    neighbour set given by boolean matrix `nbr_mask`:
        w1 * BC~  +  w2 * mean link survival  +  w3 * mean predicted lifetime / L_max
    """
    w1, w2, w3 = weights
    nodes = np.asarray(nodes, dtype=int)
    out = np.zeros(len(nodes))
    for k, v in enumerate(nodes):
        nb = nodes[nbr_mask[v, nodes]]
        nb = nb[nb != v]
        if len(nb) == 0:
            continue
        s2 = S[v, nb].mean()
        s3 = np.minimum(L[v, nb] / l_max, 1.0).mean()
        out[k] = w1 * bc_norm[k] + w2 * s2 + w3 * s3
    return out
