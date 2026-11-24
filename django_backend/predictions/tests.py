from django.test import TestCase
from predictions.ml import predict_price, predict_demand
from predictions.explanation import get_explanation

class PredictionsTests(TestCase):
    def test_predictions(self):
        input_data = {
            "cropQuality": 80,
            "price": 3000,
            "demand": 60,
            "weatherRisk": 20,
            "distance": 100,
            "transportAvailability": 80,
            "storageAvailability": 80,
        }
        future_price = predict_price(input_data)
        future_demand = predict_demand(input_data)
        self.assertGreater(future_price, 0)
        self.assertGreaterEqual(future_demand, 1)
        self.assertLessEqual(future_demand, 100)

    def test_explanation(self):
        data = {
            "weatherRisk": 75,
            "price": 60,
            "demand": 65,
            "storageAvailability": 80
        }
        explanation = get_explanation(data)
        self.assertIn("High weather risk", explanation)
        self.assertIn("Good market price", explanation)
        self.assertIn("High demand", explanation)
        self.assertIn("Sufficient storage available", explanation)

    def test_simulate_api(self):
        payload = {
            "cropQuality": 85,
            "demand": 70,
            "price": 2500,
            "weatherRisk": 40,
            "distance": 80,
            "transportAvailability": 90,
            "storageAvailability": 85
        }
        response = self.client.post('/api/simulate', payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("dpsNow", data)
        self.assertIn("dpsLater", data)
        self.assertIn("decision", data)
        self.assertIn("explanation", data)
        self.assertIn(data["decision"], ["Transport Now", "Delay Shipment"])
