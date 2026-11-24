def get_explanation(data):
    """
    Direct conversion of services/explainationService.js
    """
    reasons = []
    weather_risk = float(data.get("weatherRisk", 0))
    price = float(data.get("price", 0))
    demand = float(data.get("demand", 0))
    storage_availability = float(data.get("storageAvailability", 50))

    if weather_risk > 60:
        reasons.append("High weather risk")
    if price > 50:
        reasons.append("Good market price")
    if demand > 60:
        reasons.append("High demand")
    if storage_availability < 30:
        reasons.append("Low storage availability")
    if storage_availability > 70:
        reasons.append("Sufficient storage available")

    return ", ".join(reasons)
