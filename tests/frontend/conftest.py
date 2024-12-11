import pytest

@pytest.fixture
def mock_api_client(monkeypatch):
    def mock_get(*args, **kwargs):
        # Mock Flask-style responses
        class MockResponse:
            def get_json(self):
                return {"data": "test"}
        return MockResponse()
    monkeypatch.setattr("requests.get", mock_get) 