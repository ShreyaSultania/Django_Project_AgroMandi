from django.test import TestCase
from mandis.models import Mandi, Recommendation
from mandis.services import calculate_transport_cost

class MandisTests(TestCase):
    def setUp(self):
        Mandi.objects.create(
            name="Agra APMC",
            district="Agra",
            state="Uttar Pradesh",
            latitude=27.1767,
            longitude=78.0081
        )
        Mandi.objects.create(
            name="Mirzapur APMC",
            district="Mirzapur",
            state="Uttar Pradesh",
            latitude=25.1337,
            longitude=82.5644
        )

    def test_transport_cost_calculation(self):
        cost = calculate_transport_cost(100, 80)
        self.assertEqual(cost, round(100 * 15 * (1 + 20/100)))

    def test_recommend_mandi_api(self):
        payload = {
            "village": "Agra Rural",
            "district": "Agra",
            "state": "Uttar Pradesh",
            "commodity": "Wheat",
            "cropQuality": "A",
            "transportAvailability": "rental",
            "storageAvailability": "available",
            "quantity": 10
        }
        response = self.client.post('/api/shipments/recommend-mandi', payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        res_data = data["data"]
        self.assertIn("farmerLocation", res_data)
        self.assertIn("recommendation", res_data)
        self.assertIn("allMandis", res_data)
        self.assertGreater(len(res_data["allMandis"]), 0)

        top = res_data["recommendation"]
        self.assertIn("mandiName", top)
        self.assertIn("modalPrice", top)
        self.assertIn("transportCost", top)
        self.assertIn("netProfit", top)
        self.assertIn("bestDPS", top)
        self.assertIn("decision", top)

    def test_confirm_mandi_api_nested(self):
        payload = {
            "farmerLocation": {
                "village": "Ahirora",
                "district": "Mirzapur",
                "state": "Uttar Pradesh",
                "latitude": 25.1337,
                "longitude": 82.5644
            },
            "commodity": "Wheat",
            "quantity": 25,
            "cropQuality": "85",
            "selectedMandi": {
                "mandiName": "Ahirora APMC",
                "district": "Mirzapur",
                "distanceKm": 12.5,
                "modalPrice": 2450,
                "transportCost": 225,
                "netProfit": 61025,
                "bestDPS": 745.2,
                "decision": "Transport Now",
                "rank": 1
            },
            "weatherRisk": 35,
            "transportAvailability": "rental",
            "storageAvailability": "available",
            "totalMandisEvaluated": 5
        }
        response = self.client.post('/api/shipments/confirm-mandi', payload, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(Recommendation.objects.count(), 1)
        rec = Recommendation.objects.first()
        self.assertEqual(rec.commodity, "Wheat")
        self.assertEqual(rec.selected_mandi_name, "Ahirora APMC")

    def test_confirm_mandi_api_flat_frontend_format(self):
        payload = {
            "village": "Kharar",
            "district": "Mohali",
            "state": "Punjab",
            "commodity": "Onion",
            "quantity": 50,
            "mandiName": "Kharar APMC",
            "mandiDistrict": "Mohali",
            "modalPrice": 1500,
            "transportCost": 300,
            "netProfit": 74700,
            "decision": "Transport Now"
        }
        response = self.client.post('/api/shipments/confirm-mandi', payload, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        rec = Recommendation.objects.filter(commodity="Onion").first()
        self.assertIsNotNone(rec)
        self.assertEqual(rec.selected_mandi_name, "Kharar APMC")
