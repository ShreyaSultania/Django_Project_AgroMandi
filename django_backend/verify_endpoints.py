import os
import sys
import json
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agro_ai_backend.settings")
django.setup()

from django.test import Client

def verify_all():
    client = Client()
    print("=" * 60)
    print("STARTING FULL ENDPOINT VERIFICATION")
    print("=" * 60)

    # 1. Root /
    res = client.get('/')
    print(f"\n1. GET /: Status={res.status_code}")
    print(f"   Output: {res.content.decode()}")
    assert res.status_code == 200
    assert res.content.decode() == "Agro AI System API is running"

    # 2. Location Reverse Geocode
    res = client.get('/api/location/reverse?lat=27.1767&lon=78.0081')
    print(f"\n2. GET /api/location/reverse: Status={res.status_code}")
    print(f"   Output: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 3. Market Prices
    res = client.get('/api/prices')
    print(f"\n3. GET /api/prices: Status={res.status_code}")
    prices_data = res.json()
    print(f"   Success: {prices_data['success']}, Total Commodities: {len(prices_data['data']['prices'])}")
    print(f"   Sample item: {prices_data['data']['prices'][0]}")
    assert res.status_code == 200
    assert prices_data["success"] is True
    assert len(prices_data["data"]["prices"]) > 0

    # 4. Weather API
    res = client.get('/api/weather?city=Delhi')
    print(f"\n4. GET /api/weather?city=Delhi: Status={res.status_code}")
    weather_data = res.json()
    print(f"   Success: {weather_data.get('success')}, City: {weather_data.get('current', {}).get('name')}")
    assert res.status_code == 200
    assert weather_data["success"] is True
    assert "current" in weather_data
    assert "forecast" in weather_data

    # 5. Simulate API
    sim_payload = {
        "cropQuality": 80,
        "price": 2500,
        "demand": 65,
        "weatherRisk": 30,
        "distance": 80,
        "transportAvailability": 80,
        "storageAvailability": 70,
    }
    res = client.post('/api/simulate', data=json.dumps(sim_payload), content_type='application/json')
    print(f"\n5. POST /api/simulate: Status={res.status_code}")
    print(f"   Output: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 200
    assert "dpsNow" in res.json()
    assert "decision" in res.json()

    # 6. Recommend Mandi API
    mandi_payload = {
        "village": "Agra Rural",
        "district": "Agra",
        "state": "Uttar Pradesh",
        "commodity": "Wheat",
        "cropQuality": "A",
        "transportAvailability": "rental",
        "storageAvailability": "available",
        "quantity": 15
    }
    res = client.post('/api/shipments/recommend-mandi', data=json.dumps(mandi_payload), content_type='application/json')
    print(f"\n6. POST /api/shipments/recommend-mandi: Status={res.status_code}")
    rec_data = res.json()
    print(f"   Success: {rec_data['success']}")
    print(f"   Total mandis found: {rec_data['data']['totalMandisFound']}")
    top_mandi = rec_data['data']['recommendation']
    print(f"   Top Recommendation: {top_mandi['mandiName']} (Net Profit: {top_mandi['netProfit']}, Decision: {top_mandi['decision']}, DPS: {top_mandi['bestDPS']})")
    assert res.status_code == 200
    assert rec_data["success"] is True
    assert rec_data["data"]["totalMandisFound"] > 0

    # 7. Confirm Mandi API (Flat Frontend Format)
    confirm_payload = {
        "village": "Agra Rural",
        "district": "Agra",
        "state": "Uttar Pradesh",
        "commodity": "Wheat",
        "quantity": 15,
        "mandiName": top_mandi['mandiName'],
        "mandiDistrict": top_mandi['district'],
        "modalPrice": top_mandi['modalPrice'],
        "transportCost": top_mandi['transportCost'],
        "netProfit": top_mandi['netProfit'],
        "decision": top_mandi['decision'],
    }
    res = client.post('/api/shipments/confirm-mandi', data=json.dumps(confirm_payload), content_type='application/json')
    print(f"\n7. POST /api/shipments/confirm-mandi: Status={res.status_code}")
    print(f"   Output: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 201
    assert res.json()["success"] is True

    print("\n" + "=" * 60)
    print("ALL 7 ENDPOINTS VERIFIED AND WORKING 100% SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    verify_all()
