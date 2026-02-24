"""
ReleaseMind — Dependency Graph Parser (Phase 3)
Parses dependency.json, builds a networkx graph, and calculates:
  - Dependency depth
  - Transitive impact (blast radius)
  - Blast radius score
"""

import json
import os
from typing import Optional

try:
    import networkx as nx
    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False

DEFAULT_DEPS_PATH = os.path.join(os.path.dirname(__file__), "config", "dependency.json")

# Built-in fallback dependency graph
FALLBACK_DEPS = {
    "auth":    ["order", "payment"],
    "order":   ["payment"],
    "payment": [],
    "gateway": ["auth", "order"],
    "notification": ["order"]
}


def _load_dependency_graph(path: Optional[str] = None) -> dict:
    """Load dependency.json, fall back to built-in dict if unavailable."""
    filepath = path or DEFAULT_DEPS_PATH
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return FALLBACK_DEPS


def _build_nx_graph(deps: dict):
    """Build a directed graph from the dependency dict."""
    G = nx.DiGraph()
    for service, dependents in deps.items():
        G.add_node(service)
        for dep in dependents:
            G.add_edge(service, dep)
    return G


def _build_manual_graph(deps: dict) -> dict:
    """Lightweight graph traversal without networkx."""
    # Build reverse map: who depends ON this service?
    reverse = {}
    for svc, dependents in deps.items():
        for d in dependents:
            reverse.setdefault(d, []).append(svc)
    return reverse


def _bfs_impact(start_services: list, graph_or_deps, nx_mode: bool) -> tuple[set, int]:
    """
    Return (all_impacted_nodes, max_depth) via BFS.
    Works in both networkx and manual modes.
    """
    visited = set(start_services)
    frontier = list(start_services)
    depth = 0

    if nx_mode:
        G = graph_or_deps
        while frontier:
            next_frontier = []
            for node in frontier:
                for successor in G.successors(node):
                    if successor not in visited:
                        visited.add(successor)
                        next_frontier.append(successor)
            if next_frontier:
                depth += 1
            frontier = next_frontier
    else:
        # graph_or_deps is the raw dict
        while frontier:
            next_frontier = []
            for node in frontier:
                for successor in graph_or_deps.get(node, []):
                    if successor not in visited:
                        visited.add(successor)
                        next_frontier.append(successor)
            if next_frontier:
                depth += 1
            frontier = next_frontier

    return visited, depth


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_dependencies(
    affected_services: list,
    deps_path: Optional[str] = None
) -> dict:
    """
    Given a list of directly affected services, compute the full impact.

    Returns:
        {
          "impacted_services": list[str],
          "dependency_depth": int,
          "blast_radius_score": float,
          "impact_level": str,          # LOW | MEDIUM | HIGH | CRITICAL
          "graph_mode": str             # "networkx" | "manual"
        }
    """
    deps = _load_dependency_graph(deps_path)

    if NX_AVAILABLE:
        G = _build_nx_graph(deps)
        impacted, depth = _bfs_impact(affected_services, G, nx_mode=True)
        mode = "networkx"
    else:
        impacted, depth = _bfs_impact(affected_services, deps, nx_mode=False)
        mode = "manual"

    blast_size = len(impacted)

    # Score = each service adds weight, amplified by depth
    blast_radius_score = round(blast_size * (1 + depth * 0.5), 2)

    if blast_radius_score >= 10:
        level = "CRITICAL"
    elif blast_radius_score >= 6:
        level = "HIGH"
    elif blast_radius_score >= 3:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "impacted_services":  sorted(list(impacted)),
        "dependency_depth":   depth,
        "blast_radius_score": blast_radius_score,
        "impact_level":       level,
        "graph_mode":         mode,
        "direct_services":    affected_services
    }
