# core/tools/semantic_search.py
class SemanticSearch:
    def __init__(self, vector_store_client):
        self.client = vector_store_client

    def query(self, text: str, top_k: int = 5):
        # TODO: передать запрос в векторный индекс и получить релевантные документы
        raise NotImplementedError("SemanticSearch.query not implemented")