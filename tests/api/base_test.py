import pytest
from flask.testing import FlaskClient
from backend.flask_app import app

class BaseAPITest:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.base_url = "/api/v1" 