class MockGoogleMapsAPI:
    def get_location(self, address):
        return {
            "status": "OK",
            "lat": 37.7749,
            "lng": -122.4194,
            "formatted_address": f"Mocked address for: {address}"
        }

    def get_distance(self, origin, destination):
        return {
            "status": "OK",
            "distance": {
                "text": "5.0 km",
                "value": 5000
            },
            "duration": {
                "text": "10 mins",
                "value": 600
            }
        }
