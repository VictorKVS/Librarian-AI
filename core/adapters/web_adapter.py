# core/adapters/web_adapter.py
class WebAdapter:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def request(self, endpoint: str, data: dict):
        # TODO: реализовать HTTP-запрос к внешнему сервису
        raise NotImplementedError("WebAdapter.request not implemented")