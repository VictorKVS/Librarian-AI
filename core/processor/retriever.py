# core/processor/retriever.py
class Retriever:
    def __init__(self, vector_store_client):
        self.client = vector_store_client

    def search(self, query: str):
        # TODO: вызвать семантический поиск в векторном хранилище
        raise NotImplementedError("Retriever.search not implemented")