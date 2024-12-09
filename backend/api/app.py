from flask import Flask
from flask_restful import Api
from flask_cors import CORS

from .endpoints.route_endpoint import RouteEndpoint
from .endpoints.cost_endpoint import CostEndpoint
from .endpoints.offer_endpoint import OfferEndpoint

def create_app():
    app = Flask(__name__)
    CORS(app)
    api = Api(app)

    # Register endpoints
    api.add_resource(RouteEndpoint, '/route')
    api.add_resource(CostEndpoint, '/costs/settings')
    api.add_resource(OfferEndpoint, '/offer')

    return app

app = create_app()
