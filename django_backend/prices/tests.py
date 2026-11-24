from django.test import TestCase

class PricesTests(TestCase):
    def test_get_prices_endpoint(self):
        response = self.client.get('/api/prices')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("prices", data["data"])
        prices = data["data"]["prices"]
        self.assertIsInstance(prices, list)
        self.assertGreater(len(prices), 0)
        first = prices[0]
        self.assertIn("name", first)
        self.assertIn("price", first)
        self.assertIn("change", first)
        self.assertIn("min", first)
        self.assertIn("max", first)
