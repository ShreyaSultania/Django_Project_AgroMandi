from django.contrib import admin
from .models import Mandi, Recommendation

@admin.register(Mandi)
class MandiAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'state', 'latitude', 'longitude', 'last_updated')
    search_fields = ('name', 'district', 'state')
    list_filter = ('state',)

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('id', 'commodity', 'selected_mandi_name', 'farmer_village', 'farmer_district', 'best_dps', 'decision', 'status', 'created_at')
    search_fields = ('commodity', 'selected_mandi_name', 'farmer_village', 'farmer_district')
    list_filter = ('commodity', 'status', 'decision')
