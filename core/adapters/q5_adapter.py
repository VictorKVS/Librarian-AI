# core/adapters/q5_adapter.py
class Q5Adapter:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def query(self, params: dict):
        # TODO: интеграция с API Q5
        raise NotImplementedError("Q5Adapter.query not implemented")
