from rest_framework.views import APIView
from rest_framework.response import Response
from core.dps import calculate_dps
from .ml import predict_price, predict_demand
from .explanation import get_explanation

class SimulateView(APIView):
    """
    POST /api/simulate
    Direct conversion of controllers/simulationController.js
    """
    def post(self, request):
        data = request.data or {}

        # Scenario 1: NOW
        dps_now = calculate_dps(data)

        # Scenario 2: FUTURE
        future_data = dict(data)
        future_data["price"] = predict_price(data)
        future_data["demand"] = predict_demand(data)

        dps_later = calculate_dps(future_data)

        # Final Decision
        decision = "Transport Now" if dps_now > dps_later else "Delay Shipment"
        explanation = get_explanation(data)

        return Response({
            "dpsNow": round(dps_now, 2),
            "dpsLater": round(dps_later, 2),
            "decision": decision,
            "explanation": explanation
        })
