# core/adapters/one_c_adapter.py
class OneCAdapter:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def fetch_data(self):
        # TODO: реализовать интеграцию с 1С
        raise NotImplementedError("OneCAdapter.fetch_data not implemented")