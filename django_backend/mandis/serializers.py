from rest_framework import serializers
from .models import Mandi, Recommendation

class MandiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mandi
        fields = '__all__'


class RecommendationSerializer(serializers.ModelSerializer):
    farmerLocation = serializers.SerializerMethodField()
    selectedMandi = serializers.SerializerMethodField()
    cropQuality = serializers.CharField(source='crop_quality', read_only=True)
    weatherRisk = serializers.FloatField(source='weather_risk', read_only=True)
    transportAvailability = serializers.CharField(source='transport_availability', read_only=True)
    storageAvailability = serializers.CharField(source='storage_availability', read_only=True)
    totalMandisEvaluated = serializers.IntegerField(source='total_mandis_evaluated', read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            'id',
            'farmerLocation',
            'commodity',
            'quantity',
            'cropQuality',
            'selectedMandi',
            'weatherRisk',
            'transportAvailability',
            'storageAvailability',
            'totalMandisEvaluated',
            'status',
            'created_at',
            'updated_at',
        ]

    def get_farmerLocation(self, obj):
        return {
            "village": obj.farmer_village,
            "district": obj.farmer_district,
            "state": obj.farmer_state,
            "latitude": obj.farmer_latitude,
            "longitude": obj.farmer_longitude,
        }

    def get_selectedMandi(self, obj):
        return {
            "mandiName": obj.selected_mandi_name,
            "district": obj.selected_mandi_district,
            "distanceKm": obj.distance_km,
            "modalPrice": obj.modal_price,
            "minPrice": obj.min_price,
            "maxPrice": obj.max_price,
            "transportCost": obj.transport_cost,
            "netProfit": obj.net_profit,
            "dpsNow": obj.dps_now,
            "dpsLater": obj.dps_later,
            "bestDPS": obj.best_dps,
            "decision": obj.decision,
            "rank": obj.rank,
        }
