from django.test import TestCase
from django.urls import reverse
from core.models import Config
from core.dps import calculate_dps

class CoreTests(TestCase):
    def test_root_endpoint(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Agro AI System API is running")

    def test_socket_io_handler(self):
        response = self.client.get('/socket.io/?EIO=4&transport=polling')
        self.assertEqual(response.status_code, 200)
        self.assertIn("agro_ai_session", response.content.decode())

    def test_config_model(self):
        config = Config.get_config()
        self.assertIsNotNone(config)
        self.assertAlmostEqual(config.price, 0.3)

    def test_calculate_dps(self):
        data = {
            "cropQuality": 80,
            "demand": 70,
            "price": 2400,
            "weatherRisk": 30,
            "distance": 50,
            "transportAvailability": 80,
            "storageAvailability": 70
        }
        score = calculate_dps(data)
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
