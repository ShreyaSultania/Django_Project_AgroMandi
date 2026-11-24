from django.test import TestCase
from locations.utils import haversine_distance, KNOWN_LOCATIONS

class LocationsTests(TestCase):
    def test_haversine_distance(self):
        # Distance between New Delhi and Agra is roughly 180-210 km
        delhi_lat, delhi_lon = KNOWN_LOCATIONS["new delhi"]
        agra_lat, agra_lon = KNOWN_LOCATIONS["agra"]
        dist = haversine_distance(delhi_lat, delhi_lon, agra_lat, agra_lon)
        self.assertGreater(dist, 150)
        self.assertLess(dist, 250)

    def test_reverse_geocode_missing_params(self):
        response = self.client.get('/api/location/reverse')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])

    def test_reverse_geocode_with_known_coords(self):
        # Test near Agra
        response = self.client.get('/api/location/reverse?lat=27.1767&lon=78.0081')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("village", data["data"])
        self.assertIn("district", data["data"])
        self.assertIn("state", data["data"])
