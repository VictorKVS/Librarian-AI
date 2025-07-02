# core/tools/graph_tools.py
class GraphStore:
    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(self, node_id: str, metadata: dict):
        self.nodes.append({"id": node_id, "meta": metadata})

    def add_edge(self, src: str, dst: str, label: str):
        self.edges.append({"src": src, "dst": dst, "label": label})