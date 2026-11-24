from django.test import TestCase

class WeatherTests(TestCase):
    def test_weather_missing_params(self):
        response = self.client.get('/api/weather')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])

    def test_weather_with_city(self):
        response = self.client.get('/api/weather?city=Delhi')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("current", data)
        self.assertIn("forecast", data)
        self.assertIn("main", data["current"])
        self.assertIn("temp", data["current"]["main"])
        self.assertIn("list", data["forecast"])

    def test_weather_with_coords(self):
        response = self.client.get('/api/weather?lat=28.6139&lon=77.2090')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("current", data)
        self.assertIn("forecast", data)
