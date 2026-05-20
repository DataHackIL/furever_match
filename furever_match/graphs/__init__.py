try:
    from .match_graph import run_match_graph
except ImportError:
    def run_match_graph(request_id: str) -> dict:
        raise RuntimeError("hypergraph package not installed — use /api/v2/matches instead")

__all__ = ["run_match_graph"]
